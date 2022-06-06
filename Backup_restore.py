import os
import time
import base64
import requests
import docker
import psycopg2


class DB:
    DUMP_BIND = "/var/lib/postgresql/dump.gz"

    def __init__(self, dump: str):
        try:
            self.__password = "some_pg_password"
            self.client = docker.from_env()
            self.container = self.client.containers.run(
                "postgres:10.19",
                detach=True,
                environment={"POSTGRES_PASSWORD": self.__password},
                ports={"5432/tcp": 5432},
                volumes={dump: {"bind": self.DUMP_BIND, "mode": "rw"}},
            )
        except docker.errors.APIError as e:
            print(f"Something went wrong while starting the docker container:\n {e}")
            exit(1)

    def get_alive_ssns(self) -> list:
        with psycopg2.connect(f"host=localhost dbname=postgres user=postgres password={self.__password}") as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT ssn FROM criminal_records WHERE status LIKE 'alive'")
                return cur.fetchall()

    def finalize(self) -> None:
        self.container.stop()
        self.container.remove()

    def restore_database(self) -> None:
        try:
            result = self.container.exec_run(f"/bin/sh -c 'zcat /var/lib/postgresql/dump.gz | psql -U postgres'")
            if result.exit_code:
                print(f"Something went wrong while restoring the database:\n {result.output}")
                self.finalize()
                exit(1)
        except Exception as e:
            print(f"Something went wrong while starting the docker container:\n {e}")
            self.finalize()
            exit(1)


def configuration() -> dict:
    config = dict()
    config['access_token'] = os.getenv("BR_ACCESS_TOKEN")
    if not config['access_token']:
        raise Exception("BR_ACCESS_TOKEN is not set")
    config['current_path'] = os.path.dirname(os.path.realpath(__file__))
    return config


def get_dump_object(access_token: str) -> str:
    attempts = 5
    pause = 5
    while attempts:
        try:
            req = requests.get(
                "https://hackattic.com/challenges/backup_restore/problem",
                params={"access_token": access_token}
            )
            req.raise_for_status()
        except Exception as e:
            print(f"Something went wrong while getting the dump object {e}")
            attempts -= 1
            pause += 3
        else:
            break
    return req.json()["dump"]


def dump_to_file(dump: str, path: str, dump_file: str = "dump.gz") -> str:
    dump_path = os.path.join(path, dump_file)
    with open(dump_path, "wb") as f:
        f.write(base64.b64decode(dump))
    return dump_path


def post_alive_ssns(ssns: list) -> None:
    # No retries - if we wait, we won't pass the time limit
    try:
        resp = requests.post(
            "https://hackattic.com/challenges/backup_restore/solve",
            params={"access_token": os.getenv("BR_ACCESS_TOKEN")},
            json={"alive_ssns": ssns}
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"Something went wrong while posting the result:\n {e}")
        exit(1)
    else:
        print(f"Result posted successfully {resp}, response: {resp.text}")


def to_list(ssns: list) -> list:
    result = []
    for element in ssns:
        result.extend(element)
    return result


def main():
    config = configuration()
    # prepare the empty damp for container initialization. Docker should be
    # run before we get data from there server - there is timelimit
    dump_path = dump_to_file("", config['current_path'])
    database = DB(dump_path)
    # wait when database will be available 25 seconds guaranty that
    print("Waiting for database to be available ...")
    time.sleep(25)
    dump_object = get_dump_object(config["access_token"])
    _ = dump_to_file(dump_object, config['current_path'])
    database.restore_database()
    # sometimes I get empty dump. Maybe the right answer is [] - so I'll
    # try to check it
    alive_ssns = []
    try:
        # without retries to pass the time limit. Somtimes resource returns
        # empty database dump
        alive_ssns = to_list(database.get_alive_ssns())
    except Exception as e:
        print("Something went wrong while getting the alive SSNs:\n", e)
        database.finalize()
        exit(1)
    database.finalize()
    post_alive_ssns(alive_ssns)


if __name__ == '__main__':
    main()
