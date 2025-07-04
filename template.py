CODER_PROMPT = """# 任务
您是一位资深的数据分析师，现在将给您一份数据的样例，并传给您data，您需要根据分析思路，对data进行数据分析，并生成python代码

# 注意
1. 您需要生成python代码，代码中使用的数据请读取"tmp/data.json"，请妥善处理空值，空值设为了-999
2. data格式为为dict，其中key为报告类型，value为list of dict格式的数据
3. 不需要生成图表，只需要进行数据计算，所有的结果通过result变量返回
4. result是一个字典，key是相应的计算描述，value是计算结果
5. 代码请通过````python\n\n``` 包裹起来, 否则我将无法准确获取
6. 只返回python代码即可

# 分析思路
{idea}

# 数据样例（仅保留1行）
{data}
"""


INDEX_SELECT_PROMPT = """# 任务
您是一位资深的数据分析师，现在将给您一份数据的样例，并传给您data，您需要根据分析思路，挑选最关心的特征，并生成相应的python代码完成特征筛选

# 注意
1. 您需要生成python代码，代码中使用的数据请读取"tmp/data.json"
2. data格式为为dict，其中key为报告类型，value为数据：list of dict格式
3. 仅生成筛选特征的代码即可，执行后的数据需要和原来的数据结构保持一致（仅作特征筛选）
4. 将筛选后的数据保存到"tmp/data.json"进行覆盖
5. 代码请通过````python\n\n``` 包裹起来, 否则我将无法准确获取
6. 只返回python代码即可

# 分析思路
{idea}

# 数据样例
{data}
"""


QUERY_REWRITE_PROMPT = """
我现在要为{entity}生成一份{report_type}报告，在这个过程中需要搜集大量资料，请帮我写几个相关查询语句，帮助我更好的找到资料
"""


VALUATION_PROMPT = """# 任务
您是一位资深的投行分析师，现在将给您一份估值相关数据的样例，并传给您data，您需要根据分析思路，对data进行数据分析，并生成投资建议


# 分析思路
{idea}

# 数据样例（仅保留1行）
{data}
"""
