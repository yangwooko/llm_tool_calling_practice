import psycopg2
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class DatabaseManager:
    """데이터베이스 연결 및 쿼리 실행을 관리하는 클래스"""

    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST")
        self.port = os.getenv("POSTGRES_PORT")
        self.database = os.getenv("POSTGRES_DB")
        self.user = os.getenv("POSTGRES_USER")
        self.password = os.getenv("POSTGRES_PASS")

    def _get_connection(self):
        """데이터베이스 연결을 반환합니다."""
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )

    def execute_query(self, sql_query: str) -> Dict[str, Any]:
        """임의의 SQL 쿼리를 실행하고 결과를 List of Dict 형태로 반환합니다.

        사용 예시:
        db_manager = DatabaseManager()
        result = db_manager.execute_query("SELECT id, name, email FROM users WHERE age > 25")
        if "error" not in result:
            for user in result["results"]:
                print(f"ID: {user['id']}, Name: {user['name']}, Email: {user['email']}")
        """
        # print("🔍 SQL QUERY-->", sql_query)
        try:
            db = self._get_connection()
            cursor = db.cursor()
            cursor.execute(sql_query)
            results = cursor.fetchall()

            # 컬럼명 가져오기
            column_names = [desc[0] for desc in cursor.description]

            # List of Dict 형태로 변환
            results_dict_list = []
            for row in results:
                row_dict = dict(zip(column_names, row))
                results_dict_list.append(row_dict)

            cursor.close()
            db.close()

            return {"results": results_dict_list}

        except Exception as e:
            print(f"데이터베이스 연결 오류: {e}")
            return {"error": f"데이터베이스 연결 오류: {str(e)}"}

    def execute_query_single(self, sql_query: str) -> Dict[str, Any]:
        """단일 결과를 반환하는 SQL 쿼리를 실행합니다.

        사용 예시:
        db_manager = DatabaseManager()
        result = db_manager.execute_query_single("SELECT name FROM users WHERE id = 1")
        if "error" not in result:
            print(f"Name: {result['result']['name']}")
        """
        result = self.execute_query(sql_query)
        if "error" in result:
            return result

        if result["results"]:
            return {"result": result["results"][0]}
        else:
            return {"error": "결과가 없습니다."}

    def execute_query_count(self, sql_query: str) -> Dict[str, Any]:
        """COUNT 쿼리를 실행하고 숫자를 반환합니다.

        사용 예시:
        db_manager = DatabaseManager()
        result = db_manager.execute_query_count("SELECT COUNT(*) FROM users WHERE age > 25")
        if "error" not in result:
            print(f"Count: {result['count']}")
        """
        result = self.execute_query(sql_query)
        if "error" in result:
            return result

        if result["results"]:
            # COUNT 결과의 첫 번째 컬럼 값을 반환
            first_result = result["results"][0]
            count_value = list(first_result.values())[0]
            return {"count": count_value}
        else:
            return {"error": "결과가 없습니다."}

    def execute_query_with_params(
        self, sql_query: str, params: tuple
    ) -> Dict[str, Any]:
        """파라미터화된 SQL 쿼리를 실행합니다.

        사용 예시:
        db_manager = DatabaseManager()
        result = db_manager.execute_query_with_params(
            "SELECT * FROM users WHERE age > %s AND city = %s",
            (25, "서울")
        )
        if "error" not in result:
            for user in result["results"]:
                print(f"User: {user}")
        """
        # print("🔍 SQL QUERY-->", sql_query)
        # print("🔍 PARAMS-->", params)
        try:
            db = self._get_connection()
            cursor = db.cursor()
            cursor.execute(sql_query, params)
            results = cursor.fetchall()

            # 컬럼명 가져오기
            column_names = [desc[0] for desc in cursor.description]

            # List of Dict 형태로 변환
            results_dict_list = []
            for row in results:
                row_dict = dict(zip(column_names, row))
                results_dict_list.append(row_dict)

            cursor.close()
            db.close()

            return {"results": results_dict_list}

        except Exception as e:
            print(f"데이터베이스 연결 오류: {e}")
            return {"error": f"데이터베이스 연결 오류: {str(e)}"}

    def execute_insert(self, sql_query: str, params: tuple = None) -> Dict[str, Any]:
        """INSERT 쿼리를 실행합니다.

        사용 예시:
        db_manager = DatabaseManager()
        result = db_manager.execute_insert(
            "INSERT INTO users (name, email, age) VALUES (%s, %s, %s)",
            ("홍길동", "hong@example.com", 30)
        )
        if "error" not in result:
            print(f"Inserted rows: {result['affected_rows']}")
        """
        print("🔍 INSERT QUERY-->", sql_query)
        if params:
            print("🔍 PARAMS-->", params)

        try:
            db = self._get_connection()
            cursor = db.cursor()

            if params:
                cursor.execute(sql_query, params)
            else:
                cursor.execute(sql_query)

            affected_rows = cursor.rowcount
            db.commit()

            cursor.close()
            db.close()

            return {"affected_rows": affected_rows}

        except Exception as e:
            print(f"데이터베이스 연결 오류: {e}")
            return {"error": f"데이터베이스 연결 오류: {str(e)}"}

    def execute_update(self, sql_query: str, params: tuple = None) -> Dict[str, Any]:
        """UPDATE 쿼리를 실행합니다.

        사용 예시:
        db_manager = DatabaseManager()
        result = db_manager.execute_update(
            "UPDATE users SET age = %s WHERE id = %s",
            (31, 1)
        )
        if "error" not in result:
            print(f"Updated rows: {result['affected_rows']}")
        """
        print("🔍 UPDATE QUERY-->", sql_query)
        if params:
            print("🔍 PARAMS-->", params)

        try:
            db = self._get_connection()
            cursor = db.cursor()

            if params:
                cursor.execute(sql_query, params)
            else:
                cursor.execute(sql_query)

            affected_rows = cursor.rowcount
            db.commit()

            cursor.close()
            db.close()

            return {"affected_rows": affected_rows}

        except Exception as e:
            print(f"데이터베이스 연결 오류: {e}")
            return {"error": f"데이터베이스 연결 오류: {str(e)}"}

    def execute_delete(self, sql_query: str, params: tuple = None) -> Dict[str, Any]:
        """DELETE 쿼리를 실행합니다.

        사용 예시:
        db_manager = DatabaseManager()
        result = db_manager.execute_delete(
            "DELETE FROM users WHERE id = %s",
            (1,)
        )
        if "error" not in result:
            print(f"Deleted rows: {result['affected_rows']}")
        """
        print("🔍 DELETE QUERY-->", sql_query)
        if params:
            print("🔍 PARAMS-->", params)

        try:
            db = self._get_connection()
            cursor = db.cursor()

            if params:
                cursor.execute(sql_query, params)
            else:
                cursor.execute(sql_query)

            affected_rows = cursor.rowcount
            db.commit()

            cursor.close()
            db.close()

            return {"affected_rows": affected_rows}

        except Exception as e:
            print(f"데이터베이스 연결 오류: {e}")
            return {"error": f"데이터베이스 연결 오류: {str(e)}"}


# 전역 인스턴스 생성 (편의를 위해)
db_manager = DatabaseManager()


# 기존 함수들과의 호환성을 위한 래퍼 함수들
def execute_sql_query(sql_query: str) -> Dict[str, Any]:
    """임의의 SQL 쿼리를 실행하고 결과를 List of Dict 형태로 반환합니다."""
    return db_manager.execute_query(sql_query)


def execute_sql_query_single(sql_query: str) -> Dict[str, Any]:
    """단일 결과를 반환하는 SQL 쿼리를 실행합니다."""
    return db_manager.execute_query_single(sql_query)


def execute_sql_query_count(sql_query: str) -> Dict[str, Any]:
    """COUNT 쿼리를 실행하고 숫자를 반환합니다."""
    return db_manager.execute_query_count(sql_query)


def execute_sql_query_with_params(sql_query: str, params: tuple) -> Dict[str, Any]:
    """파라미터화된 SQL 쿼리를 실행합니다."""
    return db_manager.execute_query_with_params(sql_query, params)
