from sqlalchemy import create_engine, text, inspect
import app.database.database as database

def test_additive_migration_preserves_old_row(tmp_path, monkeypatch):
    engine = create_engine('sqlite:///' + str(tmp_path / 'old.db'))
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE forecast_checks (id INTEGER PRIMARY KEY, target_ms INTEGER)'))
        connection.execute(text('INSERT INTO forecast_checks VALUES (1, 1790000000000)'))
    monkeypatch.setattr(database, 'engine', engine)
    database.init_db()
    database.init_db()
    assert 'evaluation' in {c['name'] for c in inspect(engine).get_columns('forecast_checks')}
    with engine.connect() as connection:
        assert connection.execute(text('SELECT target_ms FROM forecast_checks')).scalar() == 1790000000000
    engine.dispose()
