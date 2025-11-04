import React, { useState, useEffect } from 'react';
import {
  Form,
  Input,
  Select,
  Button,
  Card,
  Row,
  Col,
  message,
  Alert,
  Divider
} from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import { SaveOutlined, ArrowLeftOutlined } from '@ant-design/icons';

const { Option } = Select;

interface Office {
  id: number;
  nombre: string;
}

interface UserFormData {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password?: string;
  role: string;
  telefono: string;
  cargo: string;
  oficina_id?: number;
}

const UserForm: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [offices, setOffices] = useState<Office[]>([]);
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;

  const roles = [
    { value: 'administrador', label: 'Administrador' },
    { value: 'funcionario', label: 'Funcionario' },
    { value: 'auditor', label: 'Auditor' },
    { value: 'consulta', label: 'Consulta' }
  ];

  const roleDescriptions = {
    administrador: 'Acceso completo al sistema, gestión de usuarios y configuración',
    funcionario: 'Gestión de inventario, importación/exportación de datos',
    auditor: 'Acceso de lectura y generación de reportes avanzados',
    consulta: 'Solo consulta de información básica'
  };

  useEffect(() => {
    fetchOffices();
    if (isEdit) {
      fetchUser();
    }
  }, [id]);

  const fetchOffices = async () => {
    try {
      const response = await fetch('/api/oficinas/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setOffices(data.results || data);
      }
    } catch (error) {
      console.error('Error fetching offices:', error);
    }
  };

  const fetchUser = async () => {
    try {
      const response = await fetch(`/core/api/usuarios/${id}/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const user = await response.json();
        form.setFieldsValue({
          username: user.username,
          email: user.email,
          first_name: user.first_name,
          last_name: user.last_name,
          role: user.role,
          telefono: user.profile?.telefono || '',
          cargo: user.profile?.cargo || '',
          oficina_id: user.profile?.oficina?.id,
        });
      } else {
        message.error('Error al cargar usuario');
        navigate('/app/users');
      }
    } catch (error) {
      message.error('Error de conexión');
      navigate('/app/users');
    }
  };

  const onFinish = async (values: UserFormData) => {
    setLoading(true);
    try {
      const url = isEdit 
        ? `/core/api/usuarios/${id}/` 
        : '/core/api/usuarios/crear/';
      
      const method = isEdit ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify(values),
      });

      if (response.ok) {
        message.success(`Usuario ${isEdit ? 'actualizado' : 'creado'} correctamente`);
        navigate('/app/users');
      } else {
        const errorData = await response.json();
        if (Array.isArray(errorData.error)) {
          errorData.error.forEach((error: string) => message.error(error));
        } else {
          message.error(errorData.error || 'Error al procesar solicitud');
        }
      }
    } catch (error) {
      message.error('Error de conexión');
    } finally {
      setLoading(false);
    }
  };

  const getCsrfToken = () => {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') {
        return value;
      }
    }
    return '';
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
          <Col>
            <h2>{isEdit ? 'Editar Usuario' : 'Nuevo Usuario'}</h2>
          </Col>
          <Col>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/app/users')}
            >
              Volver
            </Button>
          </Col>
        </Row>

        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{ role: 'consulta' }}
        >
          <Row gutter={24}>
            <Col span={12}>
              <h3>Información Básica</h3>
              
              {!isEdit && (
                <>
                  <Form.Item
                    label="Nombre de Usuario"
                    name="username"
                    rules={[
                      { required: true, message: 'El nombre de usuario es requerido' },
                      { min: 3, message: 'Mínimo 3 caracteres' }
                    ]}
                  >
                    <Input placeholder="Ingrese nombre de usuario" />
                  </Form.Item>

                  <Form.Item
                    label="Contraseña"
                    name="password"
                    rules={[
                      { required: true, message: 'La contraseña es requerida' },
                      { min: 8, message: 'Mínimo 8 caracteres' }
                    ]}
                  >
                    <Input.Password placeholder="Ingrese contraseña" />
                  </Form.Item>
                </>
              )}

              <Form.Item
                label="Nombres"
                name="first_name"
              >
                <Input placeholder="Ingrese nombres" />
              </Form.Item>

              <Form.Item
                label="Apellidos"
                name="last_name"
              >
                <Input placeholder="Ingrese apellidos" />
              </Form.Item>

              <Form.Item
                label="Email"
                name="email"
                rules={[
                  { type: 'email', message: 'Email inválido' }
                ]}
              >
                <Input placeholder="Ingrese email" />
              </Form.Item>
            </Col>

            <Col span={12}>
              <h3>Información Profesional</h3>
              
              <Form.Item
                label="Rol"
                name="role"
                rules={[{ required: true, message: 'El rol es requerido' }]}
              >
                <Select placeholder="Seleccione rol">
                  {roles.map(role => (
                    <Option key={role.value} value={role.value}>
                      {role.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                label="Cargo"
                name="cargo"
              >
                <Input placeholder="Ingrese cargo" />
              </Form.Item>

              <Form.Item
                label="Teléfono"
                name="telefono"
              >
                <Input placeholder="Ingrese teléfono" />
              </Form.Item>

              <Form.Item
                label="Oficina"
                name="oficina_id"
              >
                <Select placeholder="Seleccione oficina" allowClear>
                  {offices.map(office => (
                    <Option key={office.id} value={office.id}>
                      {office.nombre}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          <Alert
            message="Descripción de Roles"
            description={
              <ul style={{ marginBottom: 0 }}>
                {Object.entries(roleDescriptions).map(([role, description]) => (
                  <li key={role}>
                    <strong>{roles.find(r => r.value === role)?.label}:</strong> {description}
                  </li>
                ))}
              </ul>
            }
            type="info"
            style={{ marginBottom: '24px' }}
          />

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<SaveOutlined />}
              size="large"
            >
              {isEdit ? 'Actualizar Usuario' : 'Crear Usuario'}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default UserForm;