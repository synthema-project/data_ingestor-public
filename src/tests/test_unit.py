import unittest
from data_ingestor_utils import create_connection, save_dataset_info_to_database, get_dataset_info_from_database, remove_dataset_info_from_database
from pydantic import BaseModel

class NodeDatasetInfo(BaseModel):
    node: str
    path: str
    disease: str

class TestDataIngestor(unittest.TestCase):

    def setUp(self):
        self.node_dataset = NodeDatasetInfo(node="NODE1", path="/path/to/data", disease="DiseaseA")
        # Create an in-memory database for testing
        self.conn = sqlite3.connect(":memory:")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node TEXT NOT NULL,
                path TEXT NOT NULL,
                disease TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_save_dataset_info(self):
        save_dataset_info_to_database(self.node_dataset)
        self.cursor.execute("SELECT * FROM datasets WHERE node = ?", (self.node_dataset.node,))
        result = self.cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[1], self.node_dataset.node)

    def test_get_dataset_info(self):
        save_dataset_info_to_database(self.node_dataset)
        result = get_dataset_info_from_database(self.node_dataset.node, self.node_dataset.disease)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], self.node_dataset.node)

    def test_remove_dataset_info(self):
        save_dataset_info_to_database(self.node_dataset)
        removed = remove_dataset_info_from_database(self.node_dataset.node, self.node_dataset.disease, self.node_dataset.path)
        self.assertTrue(removed)
        result = get_dataset_info_from_database(self.node_dataset.node, self.node_dataset.disease)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
