import os
import numpy as np
import open3d as o3d
import cv2

# ================================================
# 1) 사용자 환경에 맞게 경로를 아래에 수정하세요.
# ================================================
# (A) PLY 포인트클라우드 경로
ply_path = "/Users/jeong-minuk/Downloads/person-hall/sparse/0/ply_out/points3D.ply"
# (B) COLMAP TXT 모델이 저장된 폴더 (images.txt 등이 있는 곳)
colmap_txt_dir = "/Users/jeong-minuk/Downloads/person-hall/sparse_txt"
# (C) 원본 이미지 폴더 경로
images_dir = "/Users/jeong-minuk/Downloads/person-hall/images"

# ================================================
# 2) images.txt 파싱: 카메라 회전(쿼터니언) + 이동벡터 + 이미지 파일명 읽기
# ================================================
# images.txt 형식 예시 (한 줄):
#   IMAGE_ID QW QX QY QZ TX TY TZ CAMERA_ID IMAGE_NAME
images_txt_path = os.path.join(colmap_txt_dir, "images.txt")
camera_poses = []  # [(image_name, R_mat, t_vec), ...]

with open(images_txt_path, "r") as f:
    lines = f.readlines()

for line in lines:
    line = line.strip()
    if line.startswith("#") or len(line) == 0:
        continue
    parts = line.split()
    if len(parts) < 9:
        continue
    # parts = [IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, IMAGE_NAME, ...]
    qw, qx, qy, qz = map(float, parts[1:5])
    tx, ty, tz = map(float, parts[5:8])
    image_name = parts[9]

    # Open3D가 기대하는 쿼터니언 순서: [qx, qy, qz, qw]
    R = o3d.geometry.get_rotation_matrix_from_quaternion([qx, qy, qz, qw])
    t = np.array([tx, ty, tz], dtype=np.float64)
    camera_poses.append((image_name, R, t))

# ================================================
# 3) 카메라 기즈모(축 표시) 및 위치 구슬 생성
# ================================================
camera_frames = []   # [(TriangleMesh(축 기즈모), image_name), ...]
camera_spheres = []  # [(TriangleMesh(구체), image_name), ...]

for (image_name, R, t) in camera_poses:
    # (A) 카메라 축 기즈모(주황색)
    size = 0.3  # 축 길이
    cam_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=size)
    extrinsic = np.eye(4)
    extrinsic[:3, :3] = R
    extrinsic[:3, 3] = t
    cam_frame.transform(extrinsic)
    cam_frame.paint_uniform_color([1.0, 0.7, 0.2])  # 주황색
    camera_frames.append((cam_frame, image_name))

    # (B) 카메라 위치 구슬(녹색)
    sphere = o3d.geometry.TriangleMesh.create_sphere(radius=0.1)
    sphere.translate(t)
    sphere.paint_uniform_color([0.0, 1.0, 0.0])
    camera_spheres.append((sphere, image_name))

# ================================================
# 4) 포인트클라우드 로드
# ================================================
pcd = o3d.io.read_point_cloud(ply_path)

# ================================================
# 5) 시각화: VisualizerWithEditing 실행
# ================================================
vis = o3d.visualization.VisualizerWithEditing()
vis.create_window(window_name="Person-Hall: 3D Viewer")

# (A) 포인트클라우드 추가
vis.add_geometry(pcd)

# (B) 카메라 위치(구체) 추가
for (sphere, _) in camera_spheres:
    vis.add_geometry(sphere)

# (C) 카메라 축 기즈모 추가
for (frame, _) in camera_frames:
    vis.add_geometry(frame)

# 사용자 안내 메시지
print("<< Shift + 왼쪽 클릭으로 점 하나 이상을 선택하세요. >>")
print("<< 선택을 마친 뒤, 'Q' 또는 'Esc' 키를 눌러 창을 닫으시면 됩니다. >>")
print("<< 마우스 왼쪽 버튼 드래그: 회전, 오른쪽 버튼 드래그: 이동, 휠 스크롤: 확대/축소 >>")

# This opens the window. User must use Shift+LMB to pick points,
# then press Q or Esc to close.
vis.run()

# ================================================
# 6) 윈도우가 닫힌 후, get_picked_points() 로 선택된 인덱스 얻기
# ================================================
picked_ids = vis.get_picked_points()  # [idx1, idx2, ...]
vis.destroy_window()

if len(picked_ids) == 0:
    print("선택된 포인트가 없습니다. 프로그램을 종료합니다.")
    exit()

# ================================================
# 7) 선택된 포인트 인덱스별로 가장 가까운 카메라 찾기 → 이미지 팝업
# ================================================
points = np.asarray(pcd.points)  # shape=(M,3)

# 카메라 위치 좌표만 배열로 모아 두기
cam_positions = np.vstack([t for (_, _, t) in camera_poses])  # shape=(N,3)
cam_names     = [name for (name, _, _) in camera_poses]

# “선택된 포인트” 각각에 대해, 가까운 카메라를 하나씩 찾아서 팝업
seen_images = set()  # 중복 팝업을 막기 위해

for idx in picked_ids:
    # (1) 클릭된 포인트의 3D 좌표
    pt = points[idx]

    # (2) 모든 카메라 위치와의 거리 계산
    dists = np.linalg.norm(cam_positions - pt, axis=1)
    nearest_cam_idx = np.argmin(dists)
    nearest_cam_name = cam_names[nearest_cam_idx]

    if nearest_cam_name in seen_images:
        continue  # 이미 한 번 팝업했던 이미지라면 건너뜀
    seen_images.add(nearest_cam_name)

    # (3) 해당 카메라(이미지) 파일 경로
    img_path = os.path.join(images_dir, nearest_cam_name)
    if not os.path.isfile(img_path):
        print(f"Error: 이미지 파일을 찾을 수 없습니다: {img_path}")
        continue

    # (4) OpenCV로 이미지 읽어서 팝업
    img = cv2.imread(img_path)
    if img is None:
        print(f"Error: OpenCV로 이미지를 불러오지 못했습니다: {img_path}")
        continue

    cv2.namedWindow(nearest_cam_name, cv2.WINDOW_NORMAL)
    cv2.imshow(nearest_cam_name, img)
    print(f"Displaying image: {nearest_cam_name} (Press any key to close)")
    cv2.waitKey(0)
    cv2.destroyWindow(nearest_cam_name)

print("모든 선택된 포인트에 대해 팝업을 완료했습니다. 프로그램을 종료합니다.")