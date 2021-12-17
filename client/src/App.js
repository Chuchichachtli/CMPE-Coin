import { useEffect, useState } from 'react';
import './App.css';
import 'antd/dist/antd.css';

// Util
import { wsClient } from './server/wsClient';

// Components
import { Row, Col, Divider } from 'antd';
import Node from './components/node/Node';
import { Alert } from 'antd';
import GlobalStateProvider from './utils/globalState';


function App() {
  const [status, setStatus] = useState("OFFLINE");

  useEffect(() => {
    wsClient.send({ message: 'Start connection.' });

    wsClient.status.subscribe((status) => {
      setStatus(status);
    })
  }, []);

  return (
    <GlobalStateProvider>
      <div className="App">
        <div className="status">
        {
          status === 'ONLINE' ? (
            <Alert message="CMPE Coin Network is Online." type="success" showIcon closable style={{ marginBottom: '1rem' }}/>
          ) : (
            <Alert message="CMPE Coin Network is Offline." type="warning" showIcon closable style={{ marginBottom: '1rem' }}/>
          )
        }
        </div>
        <Row gutter={16}>
          <Col span={8}>
            <Node nodeAddress={1} nodeType="Validator" />
          </Col>
          <Col span={8}>
            <Node nodeAddress={2} nodeType="Validator" />
          </Col>
          <Col span={8}>
            <Node nodeAddress={3} nodeType="Validator" />
          </Col>
        </Row>
        <Divider orientation="left"></Divider>
        <Row gutter={16}>
          <Col span={8}>
            <Node nodeAddress={4} nodeType="Simple" />
          </Col>
          <Col span={8}>
            <Node nodeAddress={5} nodeType="Simple" />
          </Col>
          <Col span={8}>
            <Node nodeAddress={6} nodeType="Simple" />
          </Col>
        </Row>
      </div>
    </GlobalStateProvider>
  );
}

export default App;
