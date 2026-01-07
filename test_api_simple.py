import os

from fastapi.testclient import TestClient

from rag_app.api import app


def main() -> None:
	repo_root = os.path.dirname(os.path.abspath(__file__))
	index_path = os.path.join(repo_root, "data", "index.joblib")

	with TestClient(app) as client:
		resp = client.post(
			"/query",
			json={
				"q": "Test API fallback",
				"per_page": 1,
				"page": 1,
				"provider": "simple",
				"index_path": index_path,
			},
		)
		print(resp.status_code)
		print(resp.json())


if __name__ == "__main__":
	main()
