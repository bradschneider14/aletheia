import React from 'react';

class PromptBanner extends React.Component{
    constructor(props){
        super(props);
    }

    render(){
        let buttons = [];
        this.props.options.forEach(element=>{
            buttons.push(
                ( <button onClick={element.action}>{element.label}</button> )
            );
        });

        return (
            <div>
                <p>{this.props.text}</p>
                {buttons}
            </div>
        );
        
    }
}

export default PromptBanner;
