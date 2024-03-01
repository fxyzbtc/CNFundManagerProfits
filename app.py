
from datetime import datetime
import numpy as np
from loguru import logger
import gradio as gr
import pandas as pd
from pipetools import pipe, X

note = '''> 备注: 
> 1. 该程序的创新之处在于，引入历史时间和规模两个权重相对真实还原了经理人真实水平，
同时有最差业绩和出勤率作为负面参考。推荐决策顺序：加权平均年化 -> 历史最差收益率 -> 出勤率 -> 总规模'。
> 2. 进度条长度对应数据分布的大致分位，可以通过拖动进度条来筛选数据。
例如，如果想要找到平均年化大于0.1的基金经理，可以将平均年化的进度条拖动到0.1以上。
> 3. 此页面的更多说明，可以参考[这里](https://mp.weixin.qq.com/s?__biz=MjM5NjA3MDUwNg==&mid=2247484566&idx=1&sn=3f354cc2f4157967d0ad5ba6a21eec74&chksm=a7e358e6d1321d318de26b993ee002db9268ec1fe1f8814e551f1d9d3e2299e2704bb865e285&scene=132&exptype=timeline_recommend_article_extendread_samebiz&poc_token=HALfzGWjDCqOTcdkqB4u2IUYLIYl0-PDlsxbnAiR)；
或者访问微信公众号【结丹记事本儿】提建议。
'''

manager_url = 'https://fund.eastmoney.com/manager/{}.html'

def load_data(manager_profits_fp="./assets/managers_profit_ayp.csv"):

    manager_profits = pd.read_csv(manager_profits_fp)
    manager_profits.columns = ['SN', 
                               '注册ID', 
                               '姓名', 
                               '总规模.亿', 
                               '职业生涯.年', 
                               '平均任职.年', 
                               '出勤率', 
                               '平均年化', 
                               '加权平均年化', 
                               '历史最差收益率']
    manager_profits = manager_profits.drop(columns=['SN'])
    
    # format the float columns to 2 decimal places
    for col in manager_profits.columns:
        if manager_profits[col].dtype is np.dtype('float64'):
            manager_profits[col] = manager_profits[col].apply(lambda x: round(x, 4))
    
    manager_profits['平均规模.亿'] = manager_profits['总规模.亿'] / (manager_profits['职业生涯.年'] * manager_profits['出勤率'])
    manager_profits['注册ID'] = manager_profits['注册ID'].apply(lambda x: f"[{x}]({manager_url.format(x)})")
    manager_profits['盈利绝对值'] = manager_profits['加权平均年化'] * manager_profits['平均规模.亿']
    manager_profits['盈利百分比'] = manager_profits['盈利绝对值'] / manager_profits['总规模.亿']
    columns = ['注册ID', '姓名', '平均规模.亿', '盈利百分比', '盈利绝对值', '总规模.亿', '出勤率',
               '职业生涯.年', '平均任职.年', '平均年化', '加权平均年化', '历史最差收益率',]
    manager_profits = manager_profits[columns]
    return manager_profits

def get_csv_mtime() -> str:
    '''get the mtime and transform it to a human readable format.'''
    import os
    mtime = os.path.getmtime("./assets/managers_profit_ayp.csv")
    mtime = datetime.fromtimestamp(mtime)
    return mtime.strftime('%Y-%m-%d %H:%M:%S')

manager_profits = load_data()
rows_of_data = manager_profits.shape[0]
updated_on = get_csv_mtime()



def slider_component(col):
    return gr.Slider(label=col, value=manager_profits[col].quantile(0.15), minimum=min(manager_profits[col]), maximum=max(manager_profits[col]), step=0.01)


def filter_data_with_slider(*args, **kwargs):
    '''Filter the data based on the input values.'''
    from copy import deepcopy
    df = deepcopy(manager_profits)
    # remember to discard the last input, which is the reg_id_or_name
    for i, value in enumerate(args, 2):
        df = df[df.iloc[:, i] >= value]
    
    return df


def filter_data_with_reg_name(*args, **kwargs):
    '''Filter the data based on the input values.'''
    from copy import deepcopy
    df = deepcopy(manager_profits)
    # filter with either reg_id or name or both of them if they are not empty

    input = ''.join(args).strip()
    if not input:
        gr.Warning('请输入注册ID或者姓名')
        return
    
    df_reg_id = df[df['注册ID'].astype(str).str.contains(input)]
    df_name = df[df['姓名'].str.contains(input)]
    
    if (df_reg_id.empty, df_name.empty) > pipe | all:
        gr.Warning('没有找到匹配的数据，请检查输入是否正确')
        return
    '''concatenate the two dataframes and drop the duplicates, then return it.
    add the head 50 is for easy comparison, if the user wants to see more, they can click the table header to sort it.'''
    return ([df_reg_id, df_name, df.head(10)] 
            > pd.concat 
            | X.drop_duplicates()
    )

def filter_data(*args, **kwargs):
    if args[-1]:
        return filter_data_with_reg_name(*args[-1], **kwargs)
    else:
        return filter_data_with_slider(*args[:-1], **kwargs)
    
with gr.Blocks(title='基金经理业绩查询') as main:
    with gr.Column():
        # add all sliders to the page
        gr.Markdown(f"```python\n{{'数据量': {rows_of_data}, '数据更新时间': {updated_on}}}\n```")
        gr.Markdown(note)
        inputs = [slider_component(col) for col in manager_profits.columns[2:]]
        reg_id_or_name = gr.Textbox(label='注册信息', placeholder='输入注册ID 或者 姓名')
        inputs.append(reg_id_or_name)

        submit_filter = gr.Button('查询')
        outputs = gr.Dataframe(label='业绩表现: (点击表头排序 | 点击注册ID查看详细信息)', value=manager_profits, datatype='markdown')

        # define the events handlers
        submit_filter.click(fn=filter_data, inputs=inputs, outputs=outputs)


        

main.launch(server_name="0.0.0.0")

# todo: 现任基金总规模，元数据中加入， https://fund.eastmoney.com/manager/30662868.html
# todo: 加入最大回撤
# todo: fix https://fund.eastmoney.com/manager/30289521.html, 出勤率错误
# todo: fix 债基，为什么收益率突变
# todo: add 当前管理基金总规模，元数据
