## roadmap
- w1: 完成企业报告生成
    - 完成数据接口开发
    - 完成web search开发
    - 完成技术框架开发
    - mvp流程跑通
- w2: 完成行业报告生成，报告样式优化
- w3: 完成宏观报告生成，报告内容优化
- w4: 效果优化



## agent 框架
- mcp_servers.py 定义工具
- corp_analysis_agent.py 调度工具通过react完成企业分析
    - tmp文件夹存放产生的中间结果
    - result文件夹存放最终结果

```bash
pip install -r requirements.txt
nohup python mcp_server.py & # 后台挂起tools服务，ps -ef | grep mcp_server 查看pid，kill -9 pid 杀掉进程
python corp_analysis_agent.py # 测试agent
```

## 代码规范
git clone仓库后，先安装依赖，再执行pre-commit install安装pre-commit钩子，每次commit代码会自动执行black和flake8格式化代码
