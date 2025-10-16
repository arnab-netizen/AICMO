import React from 'react';

const Block: React.FC<{ title: string; content: string }> = ({ title, content }) => {
    return (
        <div className="block">
            <h2>{title}</h2>
            <p>{content}</p>
        </div>
    );
};

export default Block;