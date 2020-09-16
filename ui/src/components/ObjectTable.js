import React from 'react'
import './ObjectTable.css'

class ObjectTable extends React.Component{
    constructor(props){
        super(props);
    }
 
    render(){
        if(this.props.object){
            return (
            <div className={this.props.className}>
            <table className={"propertyTable"}>
                <thead>
                    <tr>
                      <th>Property</th><th>Value</th>
                    </tr>
                </thead>
                <tbody>
                {Object.getOwnPropertyNames(this.props.object).sort().map((x)=>(<tr><td>{x}</td><td>{String(this.props.object[x])}</td></tr>))}
                </tbody>
            </table>
            </div>
            );
        }
        else{
            return "Loading...";
        }
    }
}

export default ObjectTable
