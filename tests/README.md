# Tests - GRUB Utils

## 📋 Structure des Tests (TDD)

```
tests/
├── conftest.py           # Fixtures partagées
├── unit/                 # Tests unitaires (rapides, isolés)
│   ├── core/            # Tests du core métier
│   │   ├── test_dtos.py
│   │   ├── test_facade.py
│   │   ├── test_validator.py
│   │   └── test_backup_manager.py
│   ├── services/        # Tests des services (futur)
│   └── ui/              # Tests des composants UI (futur)
├── integration/          # Tests d'intégration
│   └── test_facade_integration.py
└── e2e/                 # Tests end-to-end
    └── test_complete_workflow.py
```

## 🚀 Lancer les Tests

### Tous les tests

```bash
pytest
```

### Tests unitaires seulement

```bash
pytest -m unit
```

### Tests d'intégration

```bash
pytest -m integration
```

### Tests E2E

```bash
pytest -m e2e
```

### Exclure les tests lents

```bash
pytest -m "not slow"
```

### Avec coverage détaillé

```bash
pytest --cov=src --cov-report=html
# Ouvrir htmlcov/index.html
```

### En parallèle (plus rapide)

```bash
pytest -n auto
```

### Mode watch (relance auto)

```bash
pytest-watch
```

## 📊 Métriques de Qualité

### Coverage Target

- **Minimum**: 80%
- **Objectif**: 90%+
- **Core métier**: 95%+

### Performance

- Tests unitaires: < 0.1s chacun
- Tests d'intégration: < 1s chacun
- Tests E2E: < 5s chacun

## 🔧 TDD Workflow

### 1. Red - Écrire un test qui échoue

```python
def test_new_feature():
    """Test for new feature (not implemented yet)."""
    result = new_feature()
    assert result == expected_value
```

### 2. Green - Implémenter le minimum pour passer

```python
def new_feature():
    """Minimal implementation."""
    return expected_value
```

### 3. Refactor - Améliorer le code

```python
def new_feature():
    """Clean, optimized implementation."""
    # Refactored code with proper patterns
    return calculated_value
```

## 📝 Conventions

### Nommage

- Fichiers: `test_<module>.py`
- Classes: `TestClassName`
- Méthodes: `test_<scenario>_<expected_behavior>`

### Exemples

```python
class TestGrubFacade:
    def test_load_configuration_success(self):
        """Test successful configuration loading."""
        pass

    def test_load_configuration_file_not_found(self):
        """Test loading when config file doesn't exist."""
        pass
```

### Documentation

Chaque test doit avoir:

- Docstring expliquant le scénario
- Arrange/Act/Assert clairement séparés
- Assertions explicites avec messages

```python
def test_example(self):
    """Test that example returns correct value."""
    # Arrange
    input_value = 42

    # Act
    result = example_function(input_value)

    # Assert
    assert result == expected, f"Expected {expected}, got {result}"
```

## 🎯 Fixtures Communes

### `temp_grub_config`

Fichier de configuration GRUB temporaire

```python
def test_with_config(temp_grub_config):
    manager = GrubManager(str(temp_grub_config))
```

### `sample_grub_entries`

Configuration GRUB exemple

```python
def test_with_entries(sample_grub_entries):
    assert sample_grub_entries["GRUB_TIMEOUT"] == "5"
```

### `mock_grub_manager`

GrubManager mocké pour tests UI

```python
def test_ui_component(mock_grub_manager):
    app = GrubApp(mock_grub_manager)
```

## 🐛 Debugging

### Lancer un seul test

```bash
pytest tests/unit/core/test_facade.py::TestGrubFacade::test_load_configuration_success -v
```

### Avec debugger

```bash
pytest --pdb
```

### Voir les prints

```bash
pytest -s
```

### Mode très verbeux

```bash
pytest -vv
```

## 📚 Ressources

- [Pytest Documentation](https://docs.pytest.org/)
- [TDD by Example](https://www.obeythetestinggoat.com/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
