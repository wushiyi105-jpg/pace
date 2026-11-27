给出指定周的训练课表，只输出 JSON：
{"sessions": [{"day": "YYYY-MM-DD", "zone": "E|M|T|I|R", "km": 8}]}

- day 必须落在给定 week 的计划日期内；不确定就用 planned 里的日期；
- 只填 day / zone / km，配速由本地五区间表计算，不要自己写 pace_sec；
- 周总量比上周涨幅不超过 10%，连续两周完成率低于 60% 时先降量；
- 不写“稳住就能 PB”这类承诺。
