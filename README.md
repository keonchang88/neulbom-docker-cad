# Neulbom Docker CAD

Neulbom Docker의 FreeCAD 설계 원본과 3D 프린팅용 STL 출력물을 관리합니다.

## 관리 대상

- `FCstd/`: FreeCAD 설계 원본
- `STL/`: 3D 프린팅용 출력 파일

FreeCAD 설계를 변경한 뒤 관련 STL 파일도 다시 내보내고 같은 커밋에 포함합니다.

## 사용 준비

이 저장소는 대용량 바이너리 파일 관리를 위해 Git LFS를 사용합니다.

```bash
git lfs install
```
