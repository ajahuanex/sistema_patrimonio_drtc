import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Input,
  Select,
  Space,
  Tag,
  Modal,
  message,
  Card,
  Row,
  Col,
  Tooltip,
  Popconfirm
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  EyeOutlined,
  UserDeleteOutlined,
  CheckOutlined,
  StopOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import type { ColumnsType } from 'antd/es/table';

const { Option } = Select;

interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  role_display: string;
  is_active: boolean;
  oficina: string | null;
  cargo: string;
  created_at: string;
}

const UserList: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const navigate = useNavigate();

  const roles = [
    { value: 'administrador', label: 'Administrador' },
    { value: 'funcionario', label: 'Funcionario' },
    { value: 'auditor', label: 'Auditor' },
    { value: 'consulta', label: 'Consulta' }
  ];

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await fetch('/core/api/usuarios/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users);
      } else {
        message.error('Error al cargar usuarios');
      }
    } catch (error) {
      message.error('Error de conexión');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (userId: number, currentStatus: boolean) => {
    try {
      const response = await fetch(`/core/usuarios/${userId}/toggle-status/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-CSRFToken': getCsrfToken(),
        },
      });

      if (response.ok) {
        message.success(`Usuario ${currentStatus ? 'desactivado' : 'activado'} correctamente`);
        fetchUsers();
      } else {
        message.error('Error al cambiar estado del usuario');
      }
    } catch (error) {
      message.error('Error de conexión');
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

  const filteredUsers = users.filter(user => {
    const matchesSearch = !searchText || 
      user.username.toLowerCase().includes(searchText.toLowerCase()) ||
      user.first_name.toLowerCase().includes(searchText.toLowerCase()) ||
      user.last_name.toLowerCase().includes(searchText.toLowerCase()) ||
      user.email.toLowerCase().includes(searchText.toLowerCase());
    
    const matchesRole = !roleFilter || user.role === roleFilter;
    const matchesStatus = !statusFilter || 
      (statusFilter === 'active' && user.is_active) ||
      (statusFilter === 'inactive' && !user.is_active);

    return matchesSearch && matchesRole && matchesStatus;
  });

  const columns: ColumnsType<User> = [
    {
      title: 'Usuario',
      dataIndex: 'username',
      key: 'username',
      render: (text: string) => <strong>{text}</strong>,
    },
    {
      title: 'Nombre Completo',
      key: 'full_name',
      render: (_, record) => `${record.first_name} ${record.last_name}`.trim() || '-',
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      render: (text: string) => text || '-',
    },
    {
      title: 'Rol',
      dataIndex: 'role_display',
      key: 'role',
      render: (text: string, record) => {
        const colors = {
          administrador: 'red',
          funcionario: 'blue',
          auditor: 'green',
          consulta: 'default'
        };
        return <Tag color={colors[record.role as keyof typeof colors]}>{text}</Tag>;
      },
    },
    {
      title: 'Oficina',
      dataIndex: 'oficina',
      key: 'oficina',
      render: (text: string) => text || '-',
    },
    {
      title: 'Estado',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'success' : 'error'}>
          {active ? 'Activo' : 'Inactivo'}
        </Tag>
      ),
    },
    {
      title: 'Fecha Creación',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString('es-PE'),
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="Ver detalle">
            <Button
              type="primary"
              icon={<EyeOutlined />}
              size="small"
              onClick={() => navigate(`/app/users/${record.id}`)}
            />
          </Tooltip>
          <Tooltip title="Editar">
            <Button
              type="default"
              icon={<EditOutlined />}
              size="small"
              onClick={() => navigate(`/app/users/${record.id}/edit`)}
            />
          </Tooltip>
          <Popconfirm
            title={`¿Está seguro de ${record.is_active ? 'desactivar' : 'activar'} este usuario?`}
            onConfirm={() => handleToggleStatus(record.id, record.is_active)}
            okText="Sí"
            cancelText="No"
          >
            <Tooltip title={record.is_active ? 'Desactivar' : 'Activar'}>
              <Button
                type={record.is_active ? 'primary' : 'default'}
                danger={record.is_active}
                icon={record.is_active ? <StopOutlined /> : <CheckOutlined />}
                size="small"
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Row justify="space-between" align="middle" style={{ marginBottom: '16px' }}>
          <Col>
            <h2>Gestión de Usuarios</h2>
          </Col>
          <Col>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => navigate('/app/users/create')}
            >
              Nuevo Usuario
            </Button>
          </Col>
        </Row>

        <Row gutter={16} style={{ marginBottom: '16px' }}>
          <Col span={8}>
            <Input
              placeholder="Buscar por nombre, usuario o email..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="Filtrar por rol"
              style={{ width: '100%' }}
              value={roleFilter}
              onChange={setRoleFilter}
              allowClear
            >
              {roles.map(role => (
                <Option key={role.value} value={role.value}>
                  {role.label}
                </Option>
              ))}
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="Filtrar por estado"
              style={{ width: '100%' }}
              value={statusFilter}
              onChange={setStatusFilter}
              allowClear
            >
              <Option value="active">Activos</Option>
              <Option value="inactive">Inactivos</Option>
            </Select>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={filteredUsers}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `${range[0]}-${range[1]} de ${total} usuarios`,
          }}
        />
      </Card>
    </div>
  );
};

export default UserList;