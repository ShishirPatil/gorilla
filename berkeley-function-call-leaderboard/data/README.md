---
license: apache-2.0
language:
- en
---
# Berkeley Function Calling Leaderboard 

<!-- Provide a quick summary of the dataset. -->

The Berkeley function calling leaderboard is a live leaderboard to evaluate the ability of different LLMs to call functions (also referred to as tools). 
We built this dataset from our learnings to be representative of most users' function calling use-cases, for example, in agents, as a part of enterprise workflows, etc. 
To this end, our evaluation dataset spans diverse categories, and across multiple languages. 

Checkout the Leaderboard at [gorilla.cs.berkeley.edu/leaderboard.html](https://gorilla.cs.berkeley.edu/leaderboard.html) 
and our [release blog](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_leaderboard.html)!



## Dataset Composition

![image/png](https://cdn-uploads.huggingface.co/production/uploads/63814d392dd1f3e7bf59862f/IE-HwJL1OUSi-Tc2fT-oo.png)

| # | Category |
|---|----------|
|200 |	Chatting Capability|
|100 |	Simple (Exec)|
|50  |	Multiple (Exec)|
|50  |	Parallel (Exec)|
|40  |	Parallel & Multiple (Exec)|
|400 |	Simple (AST)|
|200 |	Multiple (AST)|
|200 |	Parallel (AST)|
|200 |	Parallel & Multiple (AST)|
|240 |	Relevance|
|70  |	REST|
|100 |	Java|
|100 |	SQL|
|50  |	Javascript|



### Dataset Description

**Chatting Capability**: In Chatting Capability, we design scenarios where no functions are passed in, and the users ask generic questions - this is similar to using the model as a general-purpose chatbot. We evaluate if the model is able to output chat messages and recognize that it does not need to invoke any functions. Note the difference with “Relevance” where the model is expected to also evaluate if any of the function input are relevant or not.

**Simple**: In simple function category, we contain the simplest but most commonly seen format: the user supplies one JSON function document, with one and only one function call will be invoked. 

**Multiple Function**: In multiple function category, a user question that only invokes one function call out of 2 - 4 JSON function documentations. The model needs to be capable of selecting the best function to invoke according to user provided context.

**Parallel Function**: Parallel function is defined as invoking multiple function calls in parallel with one user query. The model needs to digest how many function calls need to be made and the question to model can be a single sentence or multiple sentence.

**Parallel Multiple Function**: Parallel Multiple function is the combination of parallel function and multiple function. In other words, the model is provided with multiple function documentations, each of the corresponding function calls will be invoked 0 or more times. 

**Relevance (Function Relevance Detection)**: In relevance detection, we design a scenario where none of the provided functions are relevant and supposed to be invoked. We expect the model’s output to be no function call. 

**REST**: A majority of the real world API calls are from REST API calls. Python makes REST API calls through requests.get() . As a result, we include requests.get function along with a hardcoded URL and description of the purpose of the function and its parameters. Our evaluation includes two variations. The first type requires embedding the parameters inside the URL, called path parameters, for example the {Year} and {CountryCode} in  GET /api/v3/PublicHolidays/{Year}/{CountryCode}. The second type requires the model to put parameters into the params and/or headers of requests.get(.). For examples, XXX. The model is not given which type of REST API call it is going to make but needs to make a decision on how it’s going to be invoked. 
We execute all teh REST calls to evaluate correctness. 

**SQL**: SQL evaluation data includes our customized sql.execute functions that contains sql_keyword, table_name, columns, and conditions. Those four parameters provide necessary information to construct a simple SQL query like SELECT column_A from table_B where column_C == D Through this, we want to see if through function calling, SQL query can be reliably constructed and utilized rather than training a SQL specific model. 
We do not include SQL in the live leaderboard rankings, since evaluating SQL through AST or Executing them remains an open question. None-the-less, we release this hand-curated data-set 
for the benefit of the community. 

**Java and Javascript**: Despite function calling formats being the same across most programming languages, each programming language has language specific types. For example, C has pointer type, Java has HashMap type. The goal of this test category is to understand how well the function calling model can be extended to not just JSON and Python type but all the language specific typings.
We evaluate all Java and Javascript API calls through AST. 

### Evaluation Metrics

**Execute**: Everything trailing by "Exec" means that there exists an actual function or API that can be invoked for the documentation provided. As a result, the way to measure accuracy is by actually running the function call with function source code loaded.

**AST**: For all fields flagged with "AST", we match the Abstract Syntax Tree (AST) with the documentation to evaluate the answer. 




### Dataset Date

02/26/2024
 

### Organization

Gorilla LLM (UC Berkeley)

- **Created by:** Fanjia Yan, Huanzhi Mao, Charlie Cheng-Jie Ji, Ion Stoica, Joseph E. Gonzalez, Shishir G. Patil, Tianjun Zhang


### Contributing

All the models, and data used to train the models is released under Apache 2.0. 
Gorilla is an open source effort from UC Berkeley and we welcome contributors. 
Please email us your comments, criticism, and questions. 
More information about the project can be found at https://gorilla.cs.berkeley.edu/

### BibTex

```bibtex
@misc{berkeley-function-calling-leaderboard,
  title={Berkeley Function Calling Leaderboard},
  author={Fanjia Yan and Huanzhi Mao and Charlie Cheng-Jie Ji and Tianjun Zhang and Shishir G. Patil and Ion Stoica and Joseph E. Gonzalez},
  howpublished={\url{https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html}},
  year={2024},
}
```
