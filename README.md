# Person‐Hall SfM & 3D Visualization

이 리포지터리는 COLMAP을 이용해 “person-hall” 이미지 세트를 Structure-From-Motion(SfM)으로 처리한 뒤, Python(Open3D+OpenCV) 스크립트를 통해 3D 점군에서 포인트를 선택하면 해당 사진이 팝업되는 기능을 구현한 예시를 담고 있습니다.

---

## 프로젝트 구조

person-hall/
├── images/ # 원본 이미지 폴더
│ ├ img00001.jpg
│ ├ img00002.jpg
│ └ …
├── database.db # COLMAP Feature Extraction & Matching 결과 (SQLite DB)
├── sparse/
│ └ 0/
│ ├ cameras.bin # COLMAP Mapper 결과: 카메라 파라미터 바이너리
│ ├ images.bin # COLMAP Mapper 결과: 이미지별 포즈 바이너리
│ ├ points3D.bin # COLMAP Mapper 결과: 3D 포인트클라우드 바이너리
│ └ project.ini # COLMAP 프로젝트 설정
├── sparse/0/ply_out/
│ └ points3D.ply # PLY 포인트클라우드 (시각화용)
├── sparse_txt/
│ ├ cameras.txt # (TXT 형식) 카메라 내부 파라미터
│ ├ images.txt # (TXT 형식) 이미지별 쿼터니언 + 이동벡터 + 파일명
│ └ points3D.txt # (TXT 형식) 3D 포인트 정보
└── visualize_person_hall.py # Python 스크립트: 3D 뷰어에서 포인트 선택 시 사진 팝업

아래 에러가 발생한 이유는, 최신 Open3D에서 VisualizerWithEditing 객체에 더 이상 register_mouse_callback 메서드를 제공하지 않기 때문입니다. 대신, Open3D의 “Picking Mode” (Shift + 왼쪽 클릭) 기능으로 포인트를 선택한 뒤, 윈도우를 닫은 이후에 get_picked_points()를 호출하여 선택된 포인트 인덱스를 가져오는 방식을 사용해야 합니다.

Open3D 뷰어 창이 뜹니다.
Shift + 왼쪽 클릭으로 “포인트 하나 이상”을 선택하세요.
(여러 점을 골라도 됩니다. 각 점들에 가장 가까운 카메라 이미지를 찾습니다.)
사용법:
마우스 왼쪽 버튼 드래그: 씬 회전
오른쪽 버튼(또는 휠 버튼) 드래그: 씬 평행 이동
휠 스크롤: 화면 확대/축소
선택을 마쳤으면, Q(또는 Esc) 키를 눌러 뷰어 창을 닫습니다.

뷰어가 닫히면, picked_ids = vis.get_picked_points() 를 통해 “선택된 포인트 인덱스 목록”을 가져옵니다.

선택된 각 인덱스별로:

1. 해당 3D 포인트 좌표(pt)를 가져옵니다.
2. camera_poses 에서 미리 구해둔 “모든 카메라 위치 좌표”와 비교해, 가장 가까운 카메라를 찾습니다.
3. 그 카메라(이미지) 이름(파일명)을 images/ 폴더에서 찾아 OpenCV 창으로 띄웁니다.
4. 같은 이미지가 중복으로 뜨지 않도록 seen_images 집합을 만들어 관리합니다.
5. 모든 선택된 포인트에 대해 팝업을 띄우고 나면, 콘솔에 “모든 선택된 포인트에 대해 팝업을 완료했습니다. 프로그램을 종료합니다.” 라는 메시지가 출력되며 프로그램이 끝납니다.

참고자료 : https://colmap.github.io/datasets.html# (데이터 셋 활용)