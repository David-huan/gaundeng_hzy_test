背景：业务团队在快速扩张过程中，各部门反馈面试官的时间被大量无效面试占用，许多面试安排最终未能促成有效评估，导致用人部门的推进效率受到明显影响。招聘负责人希望通过分析过往的面试安排与结果数据，找出造成无效面试的核心瓶颈，减少面试资源的空耗，让面试官能够将宝贵精力集中在最值得深入沟通的候选人身上。 
 数据：interviews.csv（F:\programming\project\gaundeng\interviews.csv）： 
 
 interview_id：面试记录唯一编号 
 scheduled_at：面试邀约创建及安排的时间 
 department：发起招聘面试的用人业务部门 
 channel：候选人简历来源的具体招聘渠道 
 match_score：面试前系统综合匹配度评分 
 resume_duration_min：面试官在系统内查看简历的累计时长 
 is_valid：面试是否按期完成且为有效评估 
 口径：每次面试爽约约损失 75 工时；每提前人工复筛一次约花费 12 工时。 
 交付 
 仓根 README.md 写清：我的判断（看到了什么、根问题是什么）、做了什么、怎么证明有用（引用由数据算出的数字，并给出可复现的脚本或步骤）。 
 仓根 AI_LOG.md：关键的 AI 交互（提示词、AI 哪里不对、你怎么改的）；自己补造的数据须明确标出，不能作为结论依据。把F:\programming\project\gaundeng\test.py改为筛选适合的人的python文件，并写readme