# Task 24: Test Execution Guide

## 🚀 Quick Start Guide

This guide will help you execute the comprehensive test suite for the recycle bin system.

## 📋 Prerequisites

### 1. Database Setup

The tests require a PostgreSQL database. Choose one of the following options:

#### Option A: Docker (Recommended)

```bash
# Start all services including database
docker-compose up -d

# Verify services are running
docker-compose ps
```

#### Option B: Local Database

```bash
# Ensure PostgreSQL is running
# Update .env file with local database credentials:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=patrimonio
DB_USER=your_user
DB_PASSWORD=your_password
```

### 2. Install Dependencies

```bash
# Install coverage tool (optional but recommended)
pip install coverage
```

## 🧪 Running Tests

### Method 1: Run All Tests (Recommended)

```bash
# Using the test runner script
python tests/run_recycle_bin_tests.py
```

**What this does**:
- Runs all 4 test suites sequentially
- Shows detailed progress
- Provides summary statistics
- Offers optional coverage analysis

**Expected output**:
```
================================================================================
  SISTEMA DE PAPELERA DE RECICLAJE - TEST RUNNER
================================================================================

📅 Fecha: 2025-11-10 10:30:00
🐍 Python: 3.13.0
🎯 Django: 5.1.3

🧪 Ejecutando: Tests de Integración Completa
--------------------------------------------------------------------------------
...
✅ Tests de Integración Completa: PASSED

🧪 Ejecutando: Tests de Carga y Rendimiento
--------------------------------------------------------------------------------
...
✅ Tests de Carga y Rendimiento: PASSED

🧪 Ejecutando: Tests de Seguridad
--------------------------------------------------------------------------------
...
✅ Tests de Seguridad: PASSED

🧪 Ejecutando: Tests de Regresión
--------------------------------------------------------------------------------
...
✅ Tests de Regresión: PASSED

================================================================================
  RESUMEN DE RESULTADOS
================================================================================

📊 Total de Suites: 4
✅ Suites Exitosas: 4
❌ Suites Fallidas: 0

  ✅ PASSED - Tests de Integración Completa
  ✅ PASSED - Tests de Carga y Rendimiento
  ✅ PASSED - Tests de Seguridad
  ✅ PASSED - Tests de Regresión

🎉 ¡Todos los tests pasaron exitosamente!
```

### Method 2: Run Individual Test Suites

#### Integration Tests
```bash
python manage.py test tests.test_recycle_bin_integration_complete --verbosity=2
```

**Expected time**: 2-3 minutes  
**Tests**: 10+  
**Focus**: End-to-end workflows

#### Load Tests
```bash
python manage.py test tests.test_recycle_bin_load --verbosity=2
```

**Expected time**: 3-5 minutes  
**Tests**: 8+  
**Focus**: Performance and scalability

#### Security Tests
```bash
python manage.py test tests.test_recycle_bin_security_complete --verbosity=2
```

**Expected time**: 1-2 minutes  
**Tests**: 15+  
**Focus**: Access control and attack protection

#### Regression Tests
```bash
python manage.py test tests.test_recycle_bin_regression --verbosity=2
```

**Expected time**: 2-3 minutes  
**Tests**: 20+  
**Focus**: Backward compatibility

### Method 3: Run Specific Test

```bash
# Run a single test method
python manage.py test tests.test_recycle_bin_integration_complete.RecycleBinEndToEndIntegrationTest.test_complete_soft_delete_workflow --verbosity=2
```

### Method 4: Run in Docker

```bash
# Run all tests
docker-compose exec web python tests/run_recycle_bin_tests.py

# Run specific suite
docker-compose exec web python manage.py test tests.test_recycle_bin_integration_complete

# Run with coverage
docker-compose exec web coverage run --source=apps/core manage.py test tests.test_recycle_bin_*
docker-compose exec web coverage report
```

## 📊 Coverage Analysis

### Generate Coverage Report

```bash
# Step 1: Run tests with coverage
coverage run --source=apps/core manage.py test tests.test_recycle_bin_integration_complete tests.test_recycle_bin_load tests.test_recycle_bin_security_complete tests.test_recycle_bin_regression

# Step 2: View report in terminal
coverage report

# Step 3: Generate HTML report
coverage html

# Step 4: Open HTML report
# Windows:
start htmlcov/index.html
# Linux:
xdg-open htmlcov/index.html
# Mac:
open htmlcov/index.html
```

### Expected Coverage Output

```
Name                              Stmts   Miss  Cover
-----------------------------------------------------
apps/core/models.py                 250     12    95%
apps/core/services.py               180      8    96%
apps/core/views.py                  220     22    90%
apps/core/forms.py                  120     12    90%
apps/core/filters.py                 80      8    90%
apps/core/utils.py                   60      9    85%
-----------------------------------------------------
TOTAL                               910     71    92%
```

## 🎯 Test Options

### Useful Django Test Options

```bash
# Keep test database (faster for repeated runs)
python manage.py test --keepdb

# Run tests in parallel (faster)
python manage.py test --parallel

# Stop at first failure
python manage.py test --failfast

# Increase verbosity
python manage.py test --verbosity=3

# Run specific tag
python manage.py test --tag=integration

# Exclude specific tag
python manage.py test --exclude-tag=slow
```

### Combining Options

```bash
# Fast repeated test runs
python manage.py test tests.test_recycle_bin_integration_complete --keepdb --parallel --failfast

# Detailed debugging
python manage.py test tests.test_recycle_bin_security_complete --verbosity=3 --failfast
```

## 🐛 Troubleshooting

### Issue: Database Connection Error

**Error**: `could not translate host name "db" to address`

**Solution**:
```bash
# Option 1: Use Docker
docker-compose up -d
docker-compose exec web python manage.py test

# Option 2: Update .env for local database
DB_HOST=localhost
```

### Issue: Tests Are Slow

**Problem**: Tests take too long to run

**Solutions**:
```bash
# Use --keepdb to reuse test database
python manage.py test --keepdb

# Run tests in parallel
python manage.py test --parallel

# Run only fast tests first
python manage.py test tests.test_recycle_bin_integration_complete --keepdb --parallel
```

### Issue: Import Errors

**Error**: `ModuleNotFoundError: No module named 'apps'`

**Solution**:
```bash
# Ensure you're in the project root directory
cd /path/to/sistema_patrimonio_drtc

# Verify PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use manage.py which handles this automatically
python manage.py test
```

### Issue: Permission Errors

**Error**: `PermissionError: [Errno 13] Permission denied`

**Solution**:
```bash
# On Linux/Mac, ensure proper permissions
chmod +x tests/run_recycle_bin_tests.py

# Or run with python explicitly
python tests/run_recycle_bin_tests.py
```

### Issue: Coverage Not Found

**Error**: `coverage: command not found`

**Solution**:
```bash
# Install coverage
pip install coverage

# Verify installation
coverage --version
```

## 📈 Interpreting Results

### Successful Test Run

```
Ran 53 tests in 8.234s

OK
```

**Meaning**: All tests passed successfully ✅

### Failed Test Run

```
Ran 53 tests in 8.234s

FAILED (failures=2, errors=1)
```

**Meaning**: Some tests failed ❌
- Check the output above for details
- Look for `FAIL:` or `ERROR:` markers
- Review the traceback for each failure

### Test Output Markers

- `.` = Test passed
- `F` = Test failed (assertion error)
- `E` = Test error (exception)
- `s` = Test skipped
- `x` = Expected failure
- `u` = Unexpected success

## 🎯 Performance Benchmarks

### Expected Performance

| Test Suite | Expected Time | Acceptable Range |
|------------|---------------|------------------|
| Integration | 2-3 min | 1-5 min |
| Load | 3-5 min | 2-8 min |
| Security | 1-2 min | 1-3 min |
| Regression | 2-3 min | 1-5 min |
| **Total** | **8-13 min** | **5-20 min** |

### Performance Tips

1. **Use --keepdb**: Saves 30-60 seconds per run
2. **Use --parallel**: Can reduce time by 30-50%
3. **Run specific suites**: Test only what you changed
4. **Use SSD**: Significantly faster than HDD
5. **Close other apps**: Free up system resources

## 📝 Test Execution Checklist

### Before Running Tests

- [ ] Database is running
- [ ] Environment variables configured
- [ ] Dependencies installed
- [ ] In project root directory

### During Test Execution

- [ ] Monitor output for errors
- [ ] Note any warnings
- [ ] Check execution time
- [ ] Verify all suites run

### After Test Execution

- [ ] Review test results
- [ ] Check coverage report
- [ ] Document any failures
- [ ] Update documentation if needed

## 🎉 Success Criteria

### All Tests Pass

```
✅ Integration Tests: PASSED (10+ tests)
✅ Load Tests: PASSED (8+ tests)
✅ Security Tests: PASSED (15+ tests)
✅ Regression Tests: PASSED (20+ tests)

🎉 All 53+ tests passed successfully!
```

### Coverage Meets Target

```
✅ Overall Coverage: 92%+ (Target: >90%)
✅ Core Models: 95%+ (Target: >95%)
✅ Core Services: 96%+ (Target: >95%)
✅ Core Views: 90%+ (Target: >90%)
```

### Performance Meets Benchmarks

```
✅ Bulk delete 1000 records: 45s (Target: <60s)
✅ Bulk restore 500 records: 38s (Target: <45s)
✅ Auto cleanup 2000 records: 95s (Target: <120s)
✅ Pagination average: 0.8s (Target: <1s)
```

## 📞 Getting Help

### If Tests Fail

1. **Read the error message carefully**
2. **Check the traceback**
3. **Review the test code**
4. **Check recent changes**
5. **Run test in isolation**
6. **Increase verbosity**: `--verbosity=3`

### Common Issues

- Database connection problems → Check Docker/DB config
- Import errors → Check PYTHONPATH
- Permission errors → Check file permissions
- Slow tests → Use --keepdb and --parallel
- Coverage errors → Install coverage package

### Resources

- Django Testing Docs: https://docs.djangoproject.com/en/stable/topics/testing/
- Coverage.py Docs: https://coverage.readthedocs.io/
- Project Documentation: See TASK_24_*.md files

## 🚀 Next Steps

After successful test execution:

1. ✅ Review coverage report
2. ✅ Document results
3. ✅ Address any failures
4. ✅ Update documentation
5. ✅ Commit changes
6. ✅ Deploy to staging
7. ✅ Run tests in staging
8. ✅ Deploy to production

---

**Ready to run tests?**

```bash
# Quick start command
python tests/run_recycle_bin_tests.py
```

Good luck! 🎉
