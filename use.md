在 Python 里当库来调：                                                                                                       
```py
from agentconductor import DifficultyLevel, ProblemInstance, solve_problem                                                           
                                                                                                                                   
result = solve_problem(                                                                                                              
  ProblemInstance(
      identifier="apps-two-sum",                                                                                                   
      prompt="Write a function that returns two indices adding up to a target.",                                                   
      difficulty=DifficultyLevel.EASY,                                                                                             
  )                                                                                                                                
)                                                                                                                                    
                                                                                                                                   
print(result)                                                                                                                        
print(result.status)                                                                                                                 
print(result.max_nodes)
```                                                                                                              
                                                                                                                                   
你会拿到一个 SolveResult，里面主要有：                                                                                               
                                                                                                                                   
- problem_id                                                                                                                         
- status                                                                                                                             
- selected_difficulty                                                                                                                
- planned_turns                                                                                                                      
- max_nodes                                                                                                                          
- available_roles                                                                                                                    
- notes                                                                                                                              
                                                                                                                                   
如果你不传难度：                                                                                                                     

```py
from agentconductor import ProblemInstance, solve_problem                                                                            
                                                                                                                                   
result = solve_problem(                                                                                                              
  ProblemInstance(                                                                                                                 
      identifier="demo-1",                                                                                                         
      prompt="Solve this programming problem.",                                                                                    
  ),                                                                                                                               
  max_turns=1,                                                                                                                     
)                                                                                                                                    
```

当前会默认按 medium 处理。这是我现在的实现推断，不是论文完整逻辑。                                                                   
                                                                                                                                   
所以一句话说清楚：                                                                                                                   
现在它的用途是“定义并验证第一版可调用接口”，不是“真正完成 AgentConductor 解题流程”。                                                 
                                                                                                                                   
如果你要把它用起来，最现实的方式是：                                                                                                 
                                                                                                                                   
- 把它当成你后续系统的统一入口                                                                                                       
- 外部代码先调用 solve_problem(...)                                                                                                  
- 后面我们再把这个函数内部从“返回计划”逐步升级成“生成 topology -> 执行 agent graph -> 返回执行结果”                                  
                                                                                                                                   
如果你愿意，我下一步可以直接继续做“真正有业务价值”的下一层：                                                                         
                                                                                                                                   
1. 实现 topology schema                                                                                                              
2. 实现一个假的/规则版 orchestrator                                                                                                  
3. 实现单轮 graph 执行                                                                                                               
4. 让 solve_problem() 真正返回候选解和执行结果                                                                                       
                                                                                                                                   
这一步做完，这个项目才会开始从“接口骨架”变成“能干活的系统”。