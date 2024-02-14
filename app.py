
from datetime import datetime
import numpy as np
from loguru import logger
import gradio as gr
import pandas as pd

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


def filter_data(*args, **kwargs):
    '''Filter the data based on the input values.'''
    from copy import deepcopy
    df = deepcopy(manager_profits)
    for i, value in enumerate(args, 2):
        df = df[df.iloc[:, i] >= value]
    
    return df

with gr.Blocks(title='基金经理业绩查询') as main:
    with gr.Column():
        gr.Markdown(f"```python\n{{'数据量': {rows_of_data}, '数据更新时间': {updated_on}}}\n```")        
        inputs = [slider_component(col) for col in manager_profits.columns[2:]]
        outputs = gr.Dataframe(label='业绩表现: (点击表头排序)', value=manager_profits)
        submit_button = gr.Button('查询')
        submit_button.click(fn=filter_data, inputs=inputs, outputs=outputs)
        gr.Markdown('''> Note: 关于该页面的说明，可以在[这里](https://mp.weixin.qq.com/s?__biz=MjM5NjA3MDUwNg==&mid=2247484566&idx=1&sn=3f354cc2f4157967d0ad5ba6a21eec74&chksm=a7e358e6d1321d318de26b993ee002db9268ec1fe1f8814e551f1d9d3e2299e2704bb865e285&scene=132&exptype=timeline_recommend_article_extendread_samebiz&poc_token=HALfzGWjDCqOTcdkqB4u2IUYLIYl0-PDlsxbnAiR)找到；该页面的创新之处在于，引入历史时间和规模两个权重相对真实还原了经理人真实水平，同时有最差业绩和出勤率作为负面参考；推荐决策顺序：加权平均年化 -> 历史最差收益率 -> 出勤率 -> 总规模''')

main.launch(server_name="0.0.0.0")

