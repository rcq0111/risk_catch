import pandas as pd

def preprocess_csv_memory(df_raw):
    # 1. 전치 여부 판단
    date_check = pd.to_datetime(df_raw.index, errors='coerce').notna().all()
    lot_check = df_raw.columns.str.contains(r'[A-Za-z]').any()

    if not (date_check and lot_check):
        df_raw = df_raw.T

    # 2. NaN 채우기
    df_raw.fillna(0, inplace=True)

    # 3. index → Date 컬럼으로 이동
    df_raw.reset_index(inplace=True)

    # 4. Date 컬럼 중복 시 처리
    if 'Date' in df_raw.columns and 'index' in df_raw.columns:
        df_raw.rename(columns={"index": "Index"}, inplace=True)
    elif "index" in df_raw.columns:
        df_raw.rename(columns={"index": "Date"}, inplace=True)

    # 5. Date 컬럼 변환
    if "Date" in df_raw.columns:
        df_raw["Date"] = pd.to_datetime(df_raw["Date"], errors='coerce')
        df_raw.dropna(subset=["Date"], inplace=True)
    else:
        raise ValueError("'Date' 컬럼이 없어 datetime 변환이 불가능합니다.")

    # 6. ✅ 불필요한 인덱스 열 제거 (A열 방지)
    for col in df_raw.columns:
        if col.lower() in ['index', 'unnamed: 0']:
            df_raw.drop(columns=[col], inplace=True)

    return df_raw

