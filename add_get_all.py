import re

with open('backend/persistence/repositories/datasets.py', 'r') as f:
    text = f.read()

bad_str = '''    def get_dataset_by_name(self, name: str) -> Optional[Dataset]:'''
good_str = '''    def get_all_datasets(self) -> List[Dataset]:
        orms = self.db.query(models.DatasetORM).all()
        return [self._to_domain_dataset(orm) for orm in orms]

    def get_dataset_by_name(self, name: str) -> Optional[Dataset]:'''

text = text.replace(bad_str, good_str)

with open('backend/persistence/repositories/datasets.py', 'w') as f:
    f.write(text)
