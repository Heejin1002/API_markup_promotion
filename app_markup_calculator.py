import streamlit as st
import re
import pandas as pd
import numpy as np
from datetime import datetime

def create_multi_level_table(display_df, df, has_exchange_rate, commission_rates):
    """멀티레벨 헤더를 가진 HTML 테이블 생성 - 동적 수수료 지원"""
    # 기본 컬럼 정의
    base_cols = ['Rate ID', 'Program ID', '시작일', '종료일', '옵션명', '사이트', '대상', '넷가(바트)', '세일가(바트)']
    
    # 커미션별 컬럼 정의 (동적으로 생성)
    commission_cols_dict = {}
    for comm_rate in commission_rates:
        comm_rate_str = str(comm_rate).replace('.', '_')
        if has_exchange_rate:
            commission_cols_dict[comm_rate] = [
                f'마크업_{comm_rate_str}', 
                f'최종세일가(바트)_{comm_rate_str}%', 
                f'(원)세일가_{comm_rate_str}%',
                f'최종판매가_{comm_rate_str}%', 
                f'공급가_{comm_rate_str}%', 
                f'마진_{comm_rate_str}%(원화)'
            ]
        else:
            commission_cols_dict[comm_rate] = [
                f'마크업_{comm_rate_str}', 
                f'최종세일가(바트)_{comm_rate_str}%'
            ]
    
    # 존재하는 컬럼만 필터링
    all_commission_cols = []
    for cols in commission_cols_dict.values():
        all_commission_cols.extend(cols)
    
    all_cols = base_cols + all_commission_cols
    existing_cols = [col for col in all_cols if col in display_df.columns]
    
    # HTML 시작 - 선택 가능하고 셀 사이즈 조절 가능한 테이블
    html = """
    <style>
    .multi-header-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 0.875rem;
        margin: 1rem 0;
        user-select: text;
        -webkit-user-select: text;
        -moz-user-select: text;
        -ms-user-select: text;
    }
    .multi-header-table th {
        background-color: #f3f4f6;
        border: 1px solid #d1d5db;
        padding: 0.5rem;
        text-align: center;
        font-weight: 600;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    .multi-header-table td {
        border: 1px solid #d1d5db;
        padding: 0.5rem;
        text-align: right;
        user-select: text;
        -webkit-user-select: text;
        -moz-user-select: text;
        -ms-user-select: text;
    }
    .multi-header-table td:first-child,
    .multi-header-table td:nth-child(2),
    .multi-header-table td:nth-child(3),
    .multi-header-table td:nth-child(4),
    .multi-header-table td:nth-child(5),
    .multi-header-table td:nth-child(6),
    .multi-header-table td:nth-child(7) {
        text-align: left;
    }
    .header-top {
        background-color: #e5e7eb !important;
        font-weight: 700;
    }
    .markup-red {
        background-color: #fee2e2;
        color: #dc2626;
        font-weight: bold;
    }
    .margin-red {
        background-color: #fee2e2;
        color: #dc2626;
        font-weight: bold;
    }
    /* 마진이 마이너스인 행 전체 하이라이트 */
    .margin-red-row {
        background-color: #fee2e2 !important;
    }
    .margin-red-row td {
        background-color: #fee2e2 !important;
        color: #dc2626 !important;
        font-weight: bold !important;
    }
    /* 수수료 그룹별 구분선 - 검은색 적당한 두께 */
    .group-divider-left {
        border-left: 2px solid #000000 !important;
    }
    .group-divider-right {
        border-right: 2px solid #000000 !important;
    }
    .group-divider-top {
        border-top: 2px solid #000000 !important;
    }
    </style>
    <div style="overflow-x: auto; overflow-y: auto; max-height: 800px;">
    <table class="multi-header-table">
    """
    
    # 첫 번째 헤더 행 (커미션 그룹)
    html += "<thead><tr>"
    # 기본 컬럼들
    base_col_count = len([c for c in base_cols if c in existing_cols])
    if base_col_count > 0:
        html += f'<th colspan="{base_col_count}" class="header-top">기본 정보</th>'
    
    # 각 수수료별 그룹
    for idx, (comm_rate, cols) in enumerate(commission_cols_dict.items()):
        col_count = len([c for c in cols if c in existing_cols])
        if col_count > 0:
            html += f'<th colspan="{col_count}" class="header-top group-divider-left">수수료 {comm_rate}%</th>'
    
    html += "</tr><tr>"
    
    # 두 번째 헤더 행 (개별 컬럼명) - 그룹별 구분선 추가
    base_col_idx = 0
    commission_idx_dict = {comm_rate: 0 for comm_rate in commission_rates}
    
    for col in existing_cols:
        # 컬럼명 매핑
        col_label = col
        
        # 기본 컬럼은 그대로
        if col in base_cols:
            col_label = col
        # 동적 마크업
        elif col.startswith('마크업_'):
            col_label = '마크업'
        # 동적 세일가(바트)
        elif col.startswith('최종세일가(바트)_'):
            col_label = '세일가(바트)'
        # 동적 세일가(원)
        elif col.startswith('(원)세일가_'):
            col_label = '세일가(원)'
        # 동적 최종판매가
        elif col.startswith('최종판매가_'):
            col_label = '최종판매가'
        # 동적 공급가
        elif col.startswith('공급가_'):
            col_label = '공급가'
        # 동적 마진(원)
        elif col.startswith('마진_') and '(원화)' in col:
            col_label = '마진(원)'
        
        # 그룹별 구분선 클래스 추가
        th_class = ""
        if col in base_cols:
            base_col_idx += 1
            if base_col_idx == base_col_count and base_col_count > 0:
                th_class = "group-divider-right"
        else:
            # 어느 수수료 그룹에 속하는지 확인
            for comm_rate, cols in commission_cols_dict.items():
                if col in cols:
                    commission_idx_dict[comm_rate] += 1
                    col_count = len([c for c in cols if c in existing_cols])
                    if commission_idx_dict[comm_rate] == 1:
                        th_class = "group-divider-left"
                    elif commission_idx_dict[comm_rate] == col_count:
                        th_class = "group-divider-right"
                    break
        
        html += f'<th class="{th_class}">{col_label}</th>'
    
    html += "</tr></thead><tbody>"
    
    # 데이터 행 - 그룹별 구분선 및 마진 마이너스 행 하이라이트 추가
    for idx, row in display_df.iterrows():
        # 행 전체에 마진이 마이너스인지 확인
        has_negative_margin = False
        for col in existing_cols:
            if '(원화)' in col and '마진' in col:
                try:
                    margin_val = df.loc[idx, col]
                    if isinstance(margin_val, (int, float)) and margin_val < 0:
                        has_negative_margin = True
                        break
                except:
                    pass
        
        # 행 시작 (마진이 마이너스면 전체 행에 빨간색 배경)
        row_class = ' class="margin-red-row"' if has_negative_margin else ''
        html += f"<tr{row_class}>"
        
        base_col_idx = 0
        commission_idx_dict = {comm_rate: 0 for comm_rate in commission_rates}
        
        for col in existing_cols:
            value = row[col]
            
            # 스타일링 적용
            cell_class = ""
            
            # 마크업이 0보다 크면 빨간색 (행 하이라이트가 없을 때만)
            if not has_negative_margin and col.startswith('마크업_'):
                try:
                    markup_val = df.loc[idx, col]
                    if isinstance(markup_val, (int, float)) and markup_val > 0:
                        cell_class = 'markup-red'
                except:
                    pass
            
            # 그룹별 구분선 추가
            if col in base_cols:
                base_col_idx += 1
                if base_col_idx == base_col_count and base_col_count > 0:
                    cell_class += " group-divider-right" if cell_class else "group-divider-right"
            else:
                # 어느 수수료 그룹에 속하는지 확인
                for comm_rate, cols in commission_cols_dict.items():
                    if col in cols:
                        commission_idx_dict[comm_rate] += 1
                        col_count = len([c for c in cols if c in existing_cols])
                        if commission_idx_dict[comm_rate] == 1:
                            cell_class += " group-divider-left" if cell_class else "group-divider-left"
                        elif commission_idx_dict[comm_rate] == col_count:
                            cell_class += " group-divider-right" if cell_class else "group-divider-right"
                        break
            
            html += f'<td class="{cell_class}">{value}</td>'
        html += "</tr>"
    
    html += "</tbody></table></div>"
    return html

st.set_page_config(page_title="API 프로모션 계산", layout="wide")

def calculateRate(paxType, netPrice, salePrice, hasKrwPrice=False):
    """커미션 및 마크업 계산 - React 코드와 동일"""
    if netPrice == 0 or salePrice == 0:
        return {
            'pax_type': paxType,
            'net_price': netPrice,
            'sale_price': salePrice,
            'commission_6_6': 0,
            'supply_price_6_6': 0,
            'required_markup_6_6': 0,
            'commission_10': 0,
            'supply_price_10': 0,
            'required_markup_10': 0,
            'commission_11': 0,
            'supply_price_11': 0,
            'required_markup_11': 0
        }
    
    # 6.6% 커미션 계산 - React 코드와 동일
    import math
    commission_6_6 = round(salePrice * 0.066)
    supply_price_6_6 = salePrice - commission_6_6
    required_markup_6_6 = 0 if hasKrwPrice else (math.ceil((netPrice / supply_price_6_6 - 1) * 100) if supply_price_6_6 < netPrice else 0)
    
    # 10% 커미션 계산 - React 코드와 동일
    commission_10 = round(salePrice * 0.10)
    supply_price_10 = salePrice - commission_10
    required_markup_10 = 0 if hasKrwPrice else (math.ceil((netPrice / supply_price_10 - 1) * 100) if supply_price_10 < netPrice else 0)
    
    # 11% 커미션 계산 - React 코드와 동일
    commission_11 = round(salePrice * 0.11)
    supply_price_11 = salePrice - commission_11
    required_markup_11 = 0 if hasKrwPrice else (math.ceil((netPrice / supply_price_11 - 1) * 100) if supply_price_11 < netPrice else 0)
    
    return {
        'pax_type': paxType,
        'net_price': netPrice,
        'sale_price': salePrice,
        'commission_6_6': commission_6_6,
        'supply_price_6_6': supply_price_6_6,
        'required_markup_6_6': required_markup_6_6,
        'commission_10': commission_10,
        'supply_price_10': supply_price_10,
        'required_markup_10': required_markup_10,
        'commission_11': commission_11,
        'supply_price_11': supply_price_11,
        'required_markup_11': required_markup_11
    }

def parseHTML(html_content):
    """HTML 파싱하여 데이터 추출"""
    try:
        # 기간 추출
        period_match = re.search(r'value="(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})~(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})"', html_content)
        period = [period_match.group(1).split(' ')[0], period_match.group(2).split(' ')[0]] if period_match else ['', '']
        
        # rate_id 추출
        rate_id_match = re.search(r'name="tour_rate\.id"\s+value="(\d+)"', html_content)
        rate_id = rate_id_match.group(1) if rate_id_match else ''
        
        # 공급사 추출
        supplier_match = re.search(r'id="autoCompleteSupplier_\d+_\d+"[^>]*>([^<]+)</textarea>', html_content)
        supplier = supplier_match.group(1).strip() if supplier_match else 'N/A'
        
        programs = []
        
        # SPA 구조인지 확인
        is_spa_structure = '<tbody child-root="tour_rate.rateJson">' in html_content
        
        if is_spa_structure:
            # SPA 구조: tbody 단위로 파싱
            tbody_pattern = re.compile(r'<tbody child-root="tour_rate\.rateJson">([\s\S]*?)</tbody>')
            tbody_matches = tbody_pattern.findall(html_content)
            
            for tbody_content in tbody_matches:
                # 프로그램 ID 추출
                program_id_match = re.search(r'<input type="hidden" name="program_id" value="(\d+)"', tbody_content)
                program_id = program_id_match.group(1) if program_id_match else ''
                
                # 프로그램명 추출
                program_name_match = re.search(r'<b>([^<]+)</b>', tbody_content)
                program_name = program_name_match.group(1).strip() if program_name_match else ''
                
                # 각 행(Duration)별로 파싱
                rows = tbody_content.split('<tr')[1:]  # 첫 번째는 빈 문자열
                
                for row in rows:
                    # Duration 추출
                    duration_match = re.search(r'name="rate\.\d+\.duration"[^>]*value="(\d+)"', row)
                    duration = duration_match.group(1) if duration_match else ''
                    
                    # 옵션명 = 프로그램명 + Duration
                    option_name = f"{program_name} {duration}" if duration else program_name
                    
                    # Net 가격 추출
                    adult_nett_match = re.search(r'name="rate\.\d+\.adult\.nett"[^>]*value="(\d+)"', row)
                    adult_nett = int(adult_nett_match.group(1)) if adult_nett_match else 0
                    
                    # Sale 가격 추출 (mk만)
                    adult_sale_mk_match = re.search(r'name="rate\.\d+\.adult\.sale\.monkey\.THB"[^>]*value="(\d+)"', row)
                    adult_sale_mk = int(adult_sale_mk_match.group(1)) if adult_sale_mk_match else 0
                    
                    # KRW 가격 확인
                    adult_sale_krw_match = re.search(r'name="rate\.\d+\.adult\.sale\.monkey\.KRW"[^>]*value="(\d+)"', row)
                    adult_sale_krw = int(adult_sale_krw_match.group(1)) if adult_sale_krw_match else 0
                    
                    if adult_nett > 0 and adult_sale_mk > 0:
                        programs.append({
                            'rate_id': rate_id,
                            'program_id': program_id,
                            'program_name': option_name,
                            'site': 'mk',
                            'rates': [
                                calculateRate('성인', adult_nett, adult_sale_mk, adult_sale_krw > 0),
                                calculateRate('아동', 0, 0, False)  # SPA는 보통 아동 가격 없음
                            ]
                        })
        else:
            # 일반 투어 구조: tr 단위로 파싱
            program_pattern = re.compile(r'<input type="hidden" name="program_id" value="(\d+)"[^>]*>[\s\S]*?<b>([^<]+)</b>')
            program_infos = []
            for match in program_pattern.finditer(html_content):
                program_infos.append({
                    'id': match.group(1),
                    'name': match.group(2).strip()
                })
            
            # 각 프로그램의 가격 정보 추출
            rows = html_content.split('<tr child-root="tour_rate.rateJson">')[1:]
            
            for index, row in enumerate(rows):
                if index >= len(program_infos):
                    break
                
                program_info = program_infos[index]
                
                # Net 가격 추출
                adult_nett_match = re.search(r'name="adult\.nett"[^>]*value="(\d+)"', row)
                child_nett_match = re.search(r'name="child\.nett"[^>]*value="(\d+)"', row)
                
                adult_nett = int(adult_nett_match.group(1)) if adult_nett_match else 0
                child_nett = int(child_nett_match.group(1)) if child_nett_match else 0
                
                # Sale 가격 추출 (mk만)
                adult_sale_mk_match = re.search(r'name="adult\.sale\.monkey\.THB"[^>]*value="(\d+)"', row)
                child_sale_mk_match = re.search(r'name="child\.sale\.monkey\.THB"[^>]*value="(\d+)"', row)
                
                adult_sale_mk = int(adult_sale_mk_match.group(1)) if adult_sale_mk_match else 0
                child_sale_mk = int(child_sale_mk_match.group(1)) if child_sale_mk_match else 0
                
                # KRW 가격 확인
                adult_sale_krw_match = re.search(r'name="adult\.sale\.monkey\.KRW"[^>]*value="(\d+)"', row)
                child_sale_krw_match = re.search(r'name="child\.sale\.monkey\.KRW"[^>]*value="(\d+)"', row)
                
                adult_sale_krw = int(adult_sale_krw_match.group(1)) if adult_sale_krw_match else 0
                child_sale_krw = int(child_sale_krw_match.group(1)) if child_sale_krw_match else 0
                
                if adult_nett > 0 and adult_sale_mk > 0:
                    programs.append({
                        'rate_id': rate_id,
                        'program_id': program_info['id'],
                        'program_name': program_info['name'],
                        'site': 'mk',
                        'rates': [
                            calculateRate('성인', adult_nett, adult_sale_mk, adult_sale_krw > 0),
                            calculateRate('아동', child_nett, child_sale_mk, child_sale_krw > 0)
                        ]
                    })
        
        if len(programs) == 0:
            return None, '프로그램 데이터를 찾을 수 없습니다. HTML에 program_id와 가격 데이터가 포함되어 있는지 확인해주세요.'
        
        return {
            'basicInfo': {
                'period': {'start': period[0] or '2025-10-01', 'end': period[1] or '2026-03-31'},
                'site': 'mk (Monkey Travel)',
                'currency': 'THB',
                'supplier': supplier
            },
            'programs': programs
        }, None
        
    except Exception as e:
        return None, f'HTML 파싱 중 오류가 발생했습니다: {str(e)}'

def main():
    st.title("📊 API 프로모션 계산")
    st.markdown("### HTML 데이터 입력")
    st.info("**사용 방법:** 웹페이지에서 원하는 가격 테이블의 HTML Element 코드를 복사하여 아래에 붙여 넣으세요.")
    
    # HTML input key counter 초기화
    if 'html_input_key_counter' not in st.session_state:
        st.session_state['html_input_key_counter'] = 0
    
    # HTML 입력과 Clear 버튼을 같은 행에 배치
    col_input, col_clear = st.columns([5, 1])
    with col_input:
        html_input_key = f"html_input_value_{st.session_state['html_input_key_counter']}"
        html_input = st.text_area(
            "HTML 코드 입력",
            placeholder="여기에 HTML 코드를 붙여넣으세요...",
            height=300,
            key=html_input_key
        )
    
    with col_clear:
        st.write("")  # 공간 맞추기
        st.write("")  # 공간 맞추기
        if st.button("🗑️ Clear", use_container_width=True, key="clear_button"):
            # 키 카운터를 증가시켜 새로운 위젯으로 재생성
            st.session_state['html_input_key_counter'] += 1
            # 관련된 데이터도 초기화
            if 'parsed_data' in st.session_state:
                del st.session_state['parsed_data']
            if 'discount_rate' in st.session_state:
                st.session_state['discount_rate'] = 0
            if 'exchange_rate' in st.session_state:
                st.session_state['exchange_rate'] = 0
            if 'commission_rates' in st.session_state:
                st.session_state['commission_rates'] = []
            st.rerun()
    
    # 수수료, 환율, 할인율 입력
    col1, col2, col3 = st.columns(3)
    with col1:
        commission_rates_input = st.text_input(
            "수수료 (%)",
            value="",
            placeholder="0.00",
            help="수수료를 쉼표로 구분하여 입력하세요. (예: 6.6,10,11)"
        )
    with col2:
        exchange_rate_input = st.text_input(
            "환율 (THB → KRW)",
            value="",
            placeholder="0.00",
            help="태국 바트(THB)를 원화(KRW)로 변환할 환율을 입력하세요. (예: 1 THB = 36.5 KRW)"
        )
    with col3:
        discount_rate_input = st.text_input(
            "할인율 (%)",
            value="",
            placeholder="0.00",
            help="할인율을 입력하면 최종 판매가와 마진이 자동으로 계산됩니다."
        )
    
    if st.button("🔢 계산하기", type="primary"):
        if not html_input.strip():
            st.error("HTML 코드를 입력해주세요.")
        else:
            parsed_data, error = parseHTML(html_input)
            
            if error:
                st.error(error)
            elif parsed_data:
                # 환율과 할인율 파싱
                try:
                    exchange_rate = float(exchange_rate_input.strip()) if exchange_rate_input.strip() else 0.0
                except:
                    exchange_rate = 0.0
                    st.warning("환율 입력값이 올바르지 않습니다. 0.0으로 설정됩니다.")
                
                try:
                    discount_rate = float(discount_rate_input.strip()) if discount_rate_input.strip() else 0.0
                except:
                    discount_rate = 0.0
                    st.warning("할인율 입력값이 올바르지 않습니다. 0.0으로 설정됩니다.")
                
                st.session_state['parsed_data'] = parsed_data
                st.session_state['discount_rate'] = discount_rate
                st.session_state['exchange_rate'] = exchange_rate
                # 수수료 파싱
                try:
                    if commission_rates_input.strip():
                        commission_rates = [float(x.strip()) for x in commission_rates_input.split(',') if x.strip()]
                    else:
                        commission_rates = []
                    st.session_state['commission_rates'] = commission_rates
                except:
                    st.session_state['commission_rates'] = []
                st.success("데이터 파싱 완료!")
                st.rerun()
    
    # 결과 표시
    if 'parsed_data' in st.session_state:
        parsed_data = st.session_state['parsed_data']
        discount_rate = st.session_state.get('discount_rate', 0)
        exchange_rate = st.session_state.get('exchange_rate', 0)
        commission_rates = st.session_state.get('commission_rates', [])
        
        # 결과 영역 상단에 Clear 버튼 추가
        col_result_title, col_clear_result = st.columns([5, 1])
        with col_clear_result:
            st.write("")  # 공간 맞추기
            if st.button("🗑️ Clear All", use_container_width=True, key="clear_result_button"):
                # 모든 session_state 초기화
                st.session_state['html_input_key_counter'] += 1
                if 'parsed_data' in st.session_state:
                    del st.session_state['parsed_data']
                if 'discount_rate' in st.session_state:
                    st.session_state['discount_rate'] = 0
                if 'exchange_rate' in st.session_state:
                    st.session_state['exchange_rate'] = 0
                if 'commission_rates' in st.session_state:
                    st.session_state['commission_rates'] = []
                st.rerun()
        
        # 수수료가 없으면 경고 표시
        if not commission_rates:
            st.warning("⚠️ 수수료를 입력해주세요. 수수료 입력칸에 쉼표로 구분하여 입력하세요. (예: 6.6,10,11)")
            st.stop()
        
        # 기본 정보 및 설정 표시
        st.markdown("### 기본 정보")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("사이트", parsed_data['basicInfo']['site'])
        with col2:
            st.metric("공급사", parsed_data['basicInfo']['supplier'])
        with col3:
            st.metric("기간", f"{parsed_data['basicInfo']['period']['start']} ~ {parsed_data['basicInfo']['period']['end']}")
        with col4:
            st.metric("통화", parsed_data['basicInfo']['currency'])
        
        # 설정 정보 표시
        st.markdown("### 설정")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**할인율:** {discount_rate}%")
        with col2:
            if exchange_rate > 0:
                st.info(f"**환율:** 1 THB = {exchange_rate:,.2f} KRW")
            else:
                st.info("**환율:** 미설정")
        with col3:
            st.info(f"**수수료:** {', '.join([f'{x}%' for x in commission_rates])}")
        
        st.markdown("---")
        
        # 테이블 데이터 생성 - 수수료를 동적으로 처리
        table_rows = []
        for program in parsed_data['programs']:
            for rate in program['rates']:
                if rate['net_price'] > 0 and rate['sale_price'] > 0:
                    discount = discount_rate / 100
                    net_krw = rate['net_price'] * exchange_rate if exchange_rate > 0 else 0
                    
                    # 기본 행 데이터
                    row_data = {
                        'Rate ID': program['rate_id'],
                        'Program ID': program['program_id'],
                        '시작일': parsed_data['basicInfo']['period']['start'],
                        '종료일': parsed_data['basicInfo']['period']['end'],
                        '옵션명': program['program_name'],
                        '사이트': program['site'],
                        '대상': rate['pax_type'],
                        '넷가(바트)': rate['net_price'],
                        '세일가(바트)': rate['sale_price']
                    }
                    
                    # 각 수수료별로 동적으로 계산
                    for comm_rate in commission_rates:
                        comm_rate_str = str(comm_rate).replace('.', '_')
                        comm_rate_decimal = comm_rate / 100
                        
                        # 해당 수수료에 대한 필요 마크업 계산
                        import math
                        commission_temp = round(rate['sale_price'] * comm_rate_decimal)
                        supply_price_temp = rate['sale_price'] - commission_temp
                        has_krw_price = False  # KRW 가격이 있는지 확인 필요 (parseHTML에서 확인)
                        required_markup = 0
                        if supply_price_temp > 0 and not has_krw_price:
                            if supply_price_temp < rate['net_price']:
                                required_markup = math.ceil((rate['net_price'] / supply_price_temp - 1) * 100)
                        
                        # 필요 마크업을 사용해 최종 세일가 계산
                        req_mk = required_markup / 100
                        final_sale_thb = rate['sale_price'] * (1 + req_mk)
                        sale_krw = final_sale_thb * exchange_rate if exchange_rate > 0 else 0
                        final_price = sale_krw * (1 - discount) if exchange_rate > 0 else 0
                        commission = round(final_price * comm_rate_decimal) if exchange_rate > 0 else 0
                        supply_price = final_price - commission if exchange_rate > 0 else 0
                        margin_krw = supply_price - net_krw
                        
                        # 컬럼명 생성
                        row_data[f'마크업_{comm_rate_str}'] = required_markup
                        row_data[f'최종세일가(바트)_{comm_rate_str}%'] = round(final_sale_thb)
                        if exchange_rate > 0:
                            row_data[f'(원)세일가_{comm_rate_str}%'] = round(sale_krw)
                            row_data[f'최종판매가_{comm_rate_str}%'] = round(final_price)
                            row_data[f'공급가_{comm_rate_str}%'] = round(supply_price)
                            row_data[f'마진_{comm_rate_str}%(원화)'] = round(margin_krw)
                    
                    table_rows.append(row_data)
        
        if table_rows:
            df = pd.DataFrame(table_rows)
            # 인덱스를 0부터 시작하도록 리셋 (하이라이트 함수에서 인덱스 매칭을 위해)
            df = df.reset_index(drop=True)
            
            # 컬럼 순서 지정 (수수료별로 동적으로 그룹화, 마크업을 최종세일가 앞에 위치)
            column_order = [
                'Rate ID', 'Program ID', '시작일', '종료일', '옵션명', '사이트', '대상',
                '넷가(바트)', '세일가(바트)'
            ]
            
            # 각 수수료별로 컬럼 추가
            for comm_rate in commission_rates:
                comm_rate_str = str(comm_rate).replace('.', '_')
                if exchange_rate > 0:
                    column_order.extend([
                        f'마크업_{comm_rate_str}', f'최종세일가(바트)_{comm_rate_str}%', f'(원)세일가_{comm_rate_str}%',
                        f'최종판매가_{comm_rate_str}%', f'공급가_{comm_rate_str}%', f'마진_{comm_rate_str}%(원화)'
                    ])
                else:
                    column_order.extend([
                        f'마크업_{comm_rate_str}', f'최종세일가(바트)_{comm_rate_str}%'
                    ])
            
            # 존재하는 컬럼만 선택하여 순서 재정렬
            existing_columns = [col for col in column_order if col in df.columns]
            df = df[existing_columns]
            
            # 환율이 없으면 원화 컬럼 제거
            if exchange_rate == 0:
                krw_cols = [col for col in df.columns if '(원화)' in col]
                df = df.drop(columns=krw_cols)
            
            st.markdown(f"### 결과 테이블 (총 {len(df)}개 항목)")
            
            # 표시용 데이터프레임 (숫자 포맷팅)
            display_df = df.copy()
            # 인덱스를 0부터 시작하도록 리셋 (하이라이트 함수에서 인덱스 매칭을 위해)
            display_df = display_df.reset_index(drop=True)
            
            # 마크업 컬럼이 있으면 퍼센트 형식으로 변환 (동적으로 처리)
            for comm_rate in commission_rates:
                comm_rate_str = str(comm_rate).replace('.', '_')
                col = f'마크업_{comm_rate_str}'
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: f"{x}%" if isinstance(x, (int, float)) else x)
            
            # 숫자 컬럼 포맷팅 (동적으로 처리)
            numeric_cols = ['넷가(바트)', '세일가(바트)']
            for comm_rate in commission_rates:
                comm_rate_str = str(comm_rate).replace('.', '_')
                numeric_cols.extend([
                    f'최종세일가(바트)_{comm_rate_str}%',
                    f'(원)세일가_{comm_rate_str}%',
                    f'최종판매가_{comm_rate_str}%',
                    f'공급가_{comm_rate_str}%',
                    f'마진_{comm_rate_str}%(원화)',
                    f'마크업_{comm_rate_str}'
                ])
            
            # 원화 컬럼 (환율이 설정된 경우만, 동적으로 처리)
            krw_cols = []
            if exchange_rate > 0:
                for comm_rate in commission_rates:
                    comm_rate_str = str(comm_rate).replace('.', '_')
                    krw_cols.append(f'마진_{comm_rate_str}%(원화)')
            
            # 일반 숫자 컬럼 포맷팅
            for col in numeric_cols:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(
                        lambda x: f"{x:,}" if isinstance(x, (int, float)) and pd.notna(x) else ("" if pd.isna(x) else x)
                    )
            
            # 원화 컬럼 포맷팅 (원 단위 추가)
            for col in krw_cols:
                if col in display_df.columns:
                    # 원본 데이터프레임(df)에서 숫자 값을 가져와서 포맷팅
                    display_df[col] = df[col].apply(
                        lambda x: f"{int(x):,}원" if isinstance(x, (int, float)) and pd.notna(x) else "0원"
                    )
            
            # Streamlit dataframe으로 표시 (조절 가능한 표)
            # 행 전체 하이라이트 + 마크업 셀 하이라이트를 한 번에 처리 (덮어쓰기 문제 방지)
            def style_row(row):
                """행 전체 스타일링: 마진 음수면 행 전체 빨강, 아니면 마크업만 셀 단위 스타일"""
                row_idx = row.name
                
                # 마진이 음수인지 확인 (원본 df에서 숫자형으로 강제 변환)
                negative = False
                for col in df.columns:
                    if '마진' in col and '(원화)' in col:
                        try:
                            # 숫자형으로 강제 변환 (문자열이어도 처리)
                            v = pd.to_numeric(df.loc[row_idx, col], errors='coerce')
                            if pd.notna(v) and v < 0:
                                negative = True
                                break
                        except:
                            continue
                
                # 마진이 음수면 행 전체 빨간색 (마크업 스타일 무시)
                if negative:
                    return ['background-color: #fee2e2; color: #dc2626; font-weight: bold'] * len(row)
                
                # 마진이 음수가 아니면, 마크업만 셀 단위 스타일
                styles = [''] * len(row)
                for i, col in enumerate(row.index):
                    if col.startswith('마크업_'):
                        try:
                            # 문자열에서 % 제거 후 숫자 변환
                            val_str = str(row[col])
                            mv = float(val_str.replace('%', ''))
                            if mv > 0:
                                styles[i] = 'background-color: #fee2e2; color: #dc2626; font-weight: bold'
                        except:
                            pass
                return styles
            
            # 한 번에 스타일 적용
            styled_df = display_df.style.apply(style_row, axis=1)
            
            # Streamlit dataframe 표시
            st.dataframe(styled_df, use_container_width=True, height=600)

if __name__ == "__main__":
    main()
