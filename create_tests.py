with open('test_v1.csv', 'w', encoding='utf-8') as f:
    f.write('id,name,email,revenue\n')
    f.write('1,Alice,alice@example.com,100\n')
    f.write('2,Bob,bob@example.com,150\n')
    f.write('3,Charlie,charlie@example.com,200\n')
    f.write('4,Dave,dave@example.com,120\n')

with open('test_v2.csv', 'w', encoding='utf-8') as f:
    f.write('id,name,email,revenue,phone\n')
    f.write('1,Alice,,100,555-0101\n')
    f.write('2,Bob,,150,555-0102\n')
    f.write('3,Charlie,charlie@example.com,200,555-0103\n')
    f.write('4,Dave,dave@example.com,120,\n')

with open('test.json', 'w', encoding='utf-8') as f:
    f.write('[{"id": 1, "product": "Widget", "price": 10}, {"id": 2, "product": "Gadget", "price": 15}]')

with open('test.ndjson', 'w', encoding='utf-8') as f:
    f.write('{"id": 1, "log": "start"}\n{"id": 2, "log": "process"}\n{"id": 3, "log": "end"}\n')

with open('test_malformed.csv', 'w', encoding='utf-8') as f:
    f.write('id,name\n1,Alice\n2,Bob,extra\n')
