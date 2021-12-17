import React, { Fragment } from 'react';

// Components
import { Card, Tag, Collapse } from 'antd';
import Transaction from '../transaction/Transaction';

import './block.css';

const { Panel } = Collapse;

function Block({ block }) {
  const { prevBlockHash, currBlockHash, proofOfWork, transactions, senderNode } = block;

  return (
    <div className="block">
      <Card className="block-card" bordered={false}>
        <Tag className="block-tag" color="purple">Current Block Hash: {currBlockHash}</Tag>
        <Tag className="block-tag" color="cyan">Previous Block Hash: {prevBlockHash}</Tag>
        <Tag className="block-tag" color="gold">Proof Of Work: {proofOfWork}</Tag>
        {senderNode && <Tag className="block-tag" color="lime">Sender Node: {senderNode}</Tag>}
        <Collapse >
          <Panel header={`Transactions (${transactions.length})`} key="1">
          {transactions &&
          transactions.map((transaction, idx) => {
            return (
              <Fragment key={idx}>
                <Transaction transaction={transaction} />
              </Fragment>
            );
          })}
          </Panel>
        </Collapse>
      </Card>
    </div>
  );
}

export default Block;
