import pandas as pd

orgs = pd.read_csv("data/organizations.csv")
queries = pd.read_csv("data/organization_queries.csv")

# Группируем запросы и города по организации
grouped = queries.groupby('org_id').agg({
    'city': lambda x: '; '.join(x),
    'query': lambda y: '; '.join(y),
    'url': 'first'
}).reset_index()

result = pd.merge(orgs, grouped, on='org_id', how='left')
result.to_csv("data/final_report.csv", index=False, encoding='utf-8-sig')
print("Финальный отчёт сохранён в data/final_report.csv")