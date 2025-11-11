# Guía de Contribución

¡Gracias por tu interés en contribuir al Sistema de Registro de Patrimonio DRTC Puno!

## 🚀 Cómo Contribuir

### 1. Fork y Clone

```bash
# Fork el repositorio en GitHub
# Luego clona tu fork
git clone https://github.com/TU_USUARIO/sistema_patrimonio_drtc.git
cd sistema_patrimonio_drtc

# Agrega el repositorio original como upstream
git remote add upstream https://github.com/ORIGINAL/sistema_patrimonio_drtc.git
```

### 2. Crea una Rama

```bash
# Actualiza tu main
git checkout main
git pull upstream main

# Crea una nueva rama para tu feature
git checkout -b feature/nombre-descriptivo
```

### 3. Desarrolla

- Escribe código limpio y bien documentado
- Sigue las convenciones de estilo del proyecto
- Agrega tests para nuevas funcionalidades
- Actualiza la documentación si es necesario

### 4. Commit

```bash
# Agrega tus cambios
git add .

# Commit con mensaje descriptivo
git commit -m "feat: descripción breve del cambio

Descripción más detallada si es necesario.

Fixes #123"
```

### Convenciones de Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `docs:` Cambios en documentación
- `style:` Formato, punto y coma faltantes, etc.
- `refactor:` Refactorización de código
- `test:` Agregar o modificar tests
- `chore:` Mantenimiento, dependencias, etc.

### 5. Push y Pull Request

```bash
# Push a tu fork
git push origin feature/nombre-descriptivo

# Crea un Pull Request en GitHub
```

## 📋 Estándares de Código

### Python (Django)

- Sigue [PEP 8](https://pep8.org/)
- Usa `black` para formateo automático
- Usa `flake8` para linting
- Docstrings en todas las funciones y clases

```python
def mi_funcion(parametro: str) -> dict:
    """
    Descripción breve de la función.
    
    Args:
        parametro: Descripción del parámetro
        
    Returns:
        Descripción del retorno
    """
    pass
```

### JavaScript/TypeScript (React)

- Sigue [Airbnb Style Guide](https://github.com/airbnb/javascript)
- Usa `prettier` para formateo
- Usa `eslint` para linting
- Componentes funcionales con hooks

```typescript
interface Props {
  title: string;
  onSave: () => void;
}

export const MiComponente: React.FC<Props> = ({ title, onSave }) => {
  // Implementación
};
```

## 🧪 Tests

### Ejecutar Tests

```bash
# Python/Django
docker-compose exec web python manage.py test

# Con cobertura
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report

# JavaScript/React
cd frontend
npm test
npm run test:coverage
```

### Escribir Tests

- Todos los nuevos features deben incluir tests
- Mantén la cobertura de código > 80%
- Tests unitarios y de integración

```python
# tests/test_mi_feature.py
from django.test import TestCase

class MiFeatureTestCase(TestCase):
    def setUp(self):
        # Configuración
        pass
    
    def test_funcionalidad_basica(self):
        # Test
        self.assertEqual(resultado, esperado)
```

## 📝 Documentación

- Actualiza el README.md si es necesario
- Documenta nuevas APIs en docs/
- Agrega comentarios en código complejo
- Actualiza CHANGELOG.md

## 🔍 Revisión de Código

Tu Pull Request será revisado considerando:

- ✅ Funcionalidad correcta
- ✅ Tests pasando
- ✅ Código limpio y legible
- ✅ Documentación actualizada
- ✅ Sin conflictos con main
- ✅ Sigue los estándares del proyecto

## 🐛 Reportar Bugs

### Antes de Reportar

- Verifica que no exista un issue similar
- Asegúrate de usar la última versión
- Recopila información del error

### Template de Bug Report

```markdown
**Descripción del Bug**
Descripción clara y concisa del problema.

**Pasos para Reproducir**
1. Ve a '...'
2. Haz clic en '...'
3. Observa el error

**Comportamiento Esperado**
Qué debería suceder.

**Comportamiento Actual**
Qué sucede actualmente.

**Screenshots**
Si aplica, agrega capturas de pantalla.

**Entorno**
- OS: [e.g. Ubuntu 20.04]
- Browser: [e.g. Chrome 96]
- Versión: [e.g. 1.0.0]

**Logs**
```
Pega logs relevantes aquí
```
```

## 💡 Sugerir Features

### Template de Feature Request

```markdown
**¿El feature está relacionado con un problema?**
Descripción clara del problema.

**Solución Propuesta**
Descripción de la solución que te gustaría.

**Alternativas Consideradas**
Otras soluciones que consideraste.

**Contexto Adicional**
Cualquier otro contexto o screenshots.
```

## 📞 Contacto

- **Issues**: Usa GitHub Issues para bugs y features
- **Discusiones**: Usa GitHub Discussions para preguntas
- **Email**: dev@drtcpuno.gob.pe

## 🎯 Áreas que Necesitan Ayuda

- 📱 Mejoras en la app móvil
- 📊 Nuevos tipos de reportes
- 🌐 Internacionalización (i18n)
- 🧪 Aumentar cobertura de tests
- 📚 Mejorar documentación
- ♿ Accesibilidad (a11y)

## ✅ Checklist del Pull Request

Antes de enviar tu PR, verifica:

- [ ] El código sigue los estándares del proyecto
- [ ] He agregado tests que prueban mi cambio
- [ ] Todos los tests pasan localmente
- [ ] He actualizado la documentación
- [ ] Mi commit sigue las convenciones
- [ ] He probado en diferentes navegadores (si aplica)
- [ ] No hay conflictos con la rama main

## 🙏 Agradecimientos

¡Gracias por contribuir al proyecto! Tu ayuda es muy apreciada.

---

**Última actualización**: 11/11/2025
