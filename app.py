import streamlit as st
import os
from os.path import join
import pandas as pd
import numpy as np
import plotly.express as px
import datetime

list_reg_columns = ['정기권번호', '입차일시', '출차일시', '차량번호']
list_un_columns = ['주차권', '입차일시', '출차일시', '차량번호']
list_wd = ['월', '화', '수', '목', '금', '토', '일']

DOWNLOAD_PATH = './'
P_FILE = 'parking.xlsx'

def upload_file():
    uploaded_file = st.file_uploader('xlsx 파일을 업로드 해주세요.')
    if uploaded_file is not None:
        file_details = {"FileName":uploaded_file.name,
                        "FileType":uploaded_file.type,
                        "FileSize":uploaded_file.size}
        st.write(file_details)
        if file_details['FileName'].split('.')[-1] != 'xlsx':
            st.error('[ERROR] 파일 포맷이 엑셀(.xlsx) 가 아닙니다. 다시 업로드 해주세요.')
            return
        file_details['FileName'] = 'parking.xlsx'
        with open(join(DOWNLOAD_PATH, file_details['FileName']), 'wb') as f:
            f.write(uploaded_file.getvalue())
            write_path = join(os.path.basename(DOWNLOAD_PATH), file_details['FileName'])
            st.success(f'{write_path} is saved!')


def get_sheet(path, sheet_name):
    df_data = pd.read_excel(
                    path,
                    sheet_name=sheet_name,
                    header=0,
                    engine='openpyxl'
                    )
    if '차량번호' not in df_data.columns:
        st.error(f'[ERROR] {sheet_name} 이 올바르게 기입되지 않았습니다.')
        st.error(f'[ERROR] {sheet_name} 에 "차량번호" 를 찾을 수 없습니다.')
    if '입차일시' not in df_data.columns:
        st.error(f'[ERROR] {sheet_name} 에 "입차일시" 를 찾을 수 없습니다.')
    df_data = df_data.iloc[:, 0:4]
    df_data = df_data[df_data['차량번호'].notnull()]
    df_data['일'] = df_data['입차일시'].str.split(' ').str[0]
    df_data['시간'] = df_data['입차일시'].str.split(' ').str[-1]
    return df_data


def get_excel(path='./parking.xlsx'):
    if not os.path.exists(path):
        st.error('파일을 먼저 업로드 해주세요.')
        return None, None
    df_reg = get_sheet(path, '정기권 입차 보고서')
    df_unreg = get_sheet(path, '일반 입차 보고서')
    return df_reg, df_unreg


def calc_enter_day(df_data):
    df_data_dd = df_data.drop_duplicates(subset=['차량번호', '일'])
    df_group_car = df_data_dd.groupby('차량번호').count()['입차일시']
    df_group_car = df_group_car.sort_values(ascending=False)
    df_group_car.name = '입차일수'
    # df_group_car_thresh = df_group_car[df_group_car > 2]
    return df_group_car


def check_am_pm(str_time):
    t = int(str_time.split(':')[0])
    result = 'am' if t < 12 else 'pm'
    return result

def center_view():
    st.title('판교행복주택 주차 통계 시스템')
    restart = st.button('파일 변경')
    if restart or not os.path.exists(join(DOWNLOAD_PATH, P_FILE)):
        upload_file()
    df_reg, df_unreg = get_excel()

    str_type = st.radio('', ['등록 차량', '미등록 차량'])
    if str_type == '등록 차량':
        df_group = calc_enter_day(df_reg)
        df_cur = df_reg
    elif str_type == '미등록 차량':
        df_group = calc_enter_day(df_unreg)
        df_cur = df_unreg

    st.header(f'{str_type} 통계')
    dict_car_stat = {
        '전체 차량 수': len(df_group)
    }
    df_group_abuse = df_group[df_group >= 7]
    if str_type == '미등록 차량':
        list_abuse = list(df_group_abuse.index)
        dict_car_stat['부정주차 의심차량'] = ', '.join(list_abuse)
    st.write(dict_car_stat)

    # st.dataframe(df_group)
    st.header('최근 한 달 동안 입차한 일수')
    fig1 = px.bar(df_group_abuse)
    fig1.layout.plot_bgcolor = '#fff'
    fig1.update_yaxes(showline=True, linewidth=2, linecolor='white', gridcolor='lightgray')
    st.plotly_chart(fig1)

    st.header('차량 별 상세 입차 정보')
    car_num = st.selectbox('', list(df_group.index))
    if car_num is not None:
        df_car = df_cur[df_cur['차량번호'] == car_num]
        st.write(df_car)
        st.write({'입차일수': int(df_group.loc[car_num])})

        df_view = pd.DataFrame(columns=['날짜', '입차시간', '출입', '입차일시', '요일'])
        for i in range(len(df_car)):
            df_row = df_car.iloc[i]
            date_idx = int(df_row['일'].split('/')[-1])
            time_idx = int(df_row['시간'].split(':')[0])
            color = '입차'
            str_exact_time = df_row['입차일시']
            dt = datetime.datetime.strptime(str_exact_time, '%Y/%m/%d %H:%M')
            wd = dt.weekday()
            # np_enter[time_idx, date_idx] = '1'
            df_view.loc[i] = [date_idx, time_idx, color, str_exact_time, list_wd[wd]]

        fig = px.scatter(df_view,
                        x='날짜',
                        y='입차시간',
                        color='출입',
                        hover_data=['입차일시', '요일'],
                        labels={
                            '출입': '             출입'
                        },
                        color_discrete_map={
                            '출입':'#a67573'
                        },
                        title=f'{"- "*25}  {car_num}  {" -"*25}',
                        range_x = [0, 32],
                        range_y = [-1, 25]
                        )
        fig.update_traces(marker=dict(size=12,
                          line=dict(width=1,
                          color='black')),
                          selector=dict(mode='markers'))
        fig.layout.plot_bgcolor = '#fff'
        fig.update_xaxes(showline=True, linewidth=2, linecolor='black', gridcolor='lightgray')
        fig.update_yaxes(showline=True, linewidth=2, linecolor='black', gridcolor='lightgray')
        # fig.layout.paper_bgcolor = '#fff'
        st.plotly_chart(fig, use_container_width=False)
if __name__ == '__main__':
    center_view()
