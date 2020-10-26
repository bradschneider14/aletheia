import React from 'react';
import APIProxy from '../utils/apiProxy';
import ObjectTable from './ObjectTable';
import PromptBanner from './PromptBanner';
import ImageCanvas from './ImageCanvas';

import './AnnotationViewer.css';


class AnnotationViewer extends React.Component{
    constructor(props){
        super(props);

        this.state={
            annotation: null,
            annotationImageUrl:'',
            annotationImage: null,
            handBoxes: [],
            objectBoxes: [],
            verifiedHandBoxes: [],
        }
        
        this.getUnverifiedAnnotation = this.getUnverifiedAnnotation.bind(this);
        this.submitVerification = this.submitVerification.bind(this);
        this.submitHandBoxes = this.submitHandBoxes.bind(this);
        this.canvasBoxHandler = this.canvasBoxHandler.bind(this);
        this.submitActionCat = this.submitActionCat.bind(this);
    }

    componentDidMount(){
        this.getUnverifiedAnnotation();
    }

    getUnverifiedAnnotation(){
        APIProxy.getUrl('/annotation?verified=False&LIMIT=1',
            (json) => {
                const the_annotation = json.annotations[0];
                const handBoxes = [];
                const objectBoxes = [];

                const annHandBoxes = JSON.parse(the_annotation.hand_boxes) || []
                annHandBoxes.forEach((hand)=>{
                    handBoxes.push({
                        x0: hand[0][0],
                        x1: hand[1][0],
                        y0: hand[0][1],
                        y1: hand[1][1],
                        color: 'green',
                    });
                });

                if(the_annotation.obj_bounds){
                    // bit of a hack, but we expect a string like "[ 'xx', 'yy', ...]" and JSON won't parse with the single quotes
                    const boundsString = the_annotation.obj_bounds.replace(/\'/g, '');
                    const bounds = JSON.parse(boundsString);
                    let start = 0;
                    while(start < bounds.length){
                        objectBoxes.push({
                            x0: bounds[1+start],
                            x1: bounds[1+start] + bounds[3+start],
                            y0: bounds[0+start],
                            y1: bounds[0+start] + bounds[2+start],
                            color: 'blue',
                        });

                        start = start + 4;
                    }
                }
                
                this.setState(
                    {
                        annotation: the_annotation,
                        annotationImageUrl: `annotation/${the_annotation.id}/image`,
                        annotationImage: null,
                        handBoxes: handBoxes,
                        objectBoxes: objectBoxes,
                        verifiedHandBoxes: []
                    }
                );
                APIProxy.getRawUrl(`annotation/${json.annotations[0].id}/image`,
                    (response) => {
                        let fileReader = new FileReader();
                        fileReader.readAsDataURL(response);
                        fileReader.onload = () => {
                            this.setState({
                                annotationImage: fileReader.result,
                             });
                        };
                    },
                    (error) => {
                        console.log(`Failed to get annotation image: ${error}`);
                    }
                );
            },
            (error) => {
                console.log(`Failed to get annotations: ${error}`);
            }
        );
    }

    submitVerification(isValid){
        let theData = {verified: true, is_valid: isValid}
        APIProxy.putUrl(`annotation/${this.state.annotation.id}`, theData,
            (resp) => {
                if(this.state.annotation){
                    this.setState({
                        annotation: Object.assign(this.state.annotation, theData),
                    });
                }
            },
            (error) => console.log('Failed to submit verification: ' + error)
        );
    }

    submitActionCat(verbCat){
        let theData = {verb_cat: verbCat}
        APIProxy.putUrl(`annotation/${this.state.annotation.id}`, theData,
            (resp) => {
                if(this.state.annotation){
                    this.setState({
                        annotation: Object.assign(this.state.annotation, theData),
                        drawingEnabled: true,
                    });
                }
            },
            (error) => console.log('Failed to submit action category: ' + error)
        );
    }

    submitHandBoxes(){
        let theData = {verified_hands: this.state.verifiedHandBoxes.map(box=>[[box.x0, box.y0], [box.x1, box.y1]])};
        APIProxy.putUrl(`annotation/${this.state.annotation.id}`, theData,
            (resp) => {
                if(this.state.annotation){
                    this.setState({
                        annotation: Object.assign(this.state.annotation, theData),
                        drawingEnabled: false,
                    });
                }
            },
            (error) => console.log('Failed to submit verification: ' + error)
        );
    }

    canvasBoxHandler(left, right, top, bottom){
        this.setState((prevState) => {
            return {verifiedHandBoxes: [...prevState.verifiedHandBoxes, {x0:left, x1:right, y0:top, y1:bottom, color:'red'}]}
        });
    }

    render(){
        let topBox;
        let imageArea;    

        if(this.state.annotation){
            if(!this.state.annotation['verified']){
                let actionPhrase = ''
                if(this.state.annotation['verb'] && this.state.annotation['obj_name']){
                    actionPhrase = `(${this.state.annotation['verb']} ${this.state.annotation['obj_name']})`;
                }    

                const promptStr = `Does the action appear to be correct? ${actionPhrase}`;

                topBox = (
                    <PromptBanner
                        text={promptStr}
                        options={[
                            { 
                                label:'no',
                                action: ()=>{this.submitVerification(false)}
                            },
                            {
                                label:'yes',
                                action: ()=>{ this.submitVerification(true)}
                            },
                        ]}
                    />
                );

                imageArea = (
                    <img 
                        src={this.state.annotationImage ? this.state.annotationImage : require('../images/loading.gif')}
                        style={{maxWidth:"100%", maxHeight:"100%"}}
                    />
                );
            }

        else if(!this.state.annotation['verb_cat']){
                topBox = (
                    <PromptBanner
                        text='Which verb category is most descriptive of the action?'
                        options={[
                            { 
                                label:'Interact',
                                action: ()=>{this.submitActionCat('interact')}
                            },
                            {
                                label:'Modify',
                                action: ()=>{ this.submitActionCat('modify')}
                            },
                            {
                                label:'Relocate',
                                action: ()=>{ this.submitActionCat('relocate')}
                            },
                            {
                                label:'None',
                                action: ()=>{ this.submitActionCat('none')}
                            },
                        ]}
                    />
                );

                imageArea = (
                    <img 
                        src={this.state.annotationImage ? this.state.annotationImage : require('../images/loading.gif')}
                        style={{maxWidth:"100%", maxHeight:"100%"}}
                    />
                );
            }
            else if(!this.state.annotation['verified_hands']){
                topBox = (
                    <PromptBanner
                        text='Please draw a box over the region(s) containing hands (separate boxes for each hand), capturing up to the wrist if visible.'
                        options={[
                            {
                                label:'Clear',
                                action: ()=>{ this.setState({verifiedHandBoxes:[]})  }
                            },
                            {
                                label:'Submit',
                                action: ()=>{ this.submitHandBoxes() }
                            },
                        ]}
                    />
                );

                imageArea = (
                    <ImageCanvas
                        drawingEnabled={this.state.drawingEnabled}
                        imageSrc={this.state.annotationImage ? this.state.annotationImage : require('../images/loading.gif')}
                        style={{maxWidth:"100%", maxHeight:"100%"}}
                        boxHandler={this.canvasBoxHandler}
                        boxes={[...this.state.handBoxes, ...this.state.objectBoxes, ...this.state.verifiedHandBoxes]}
                    />
                );
            }
            else{
                topBox = (
                    <PromptBanner
                        text = 'Thank you for your submission!'
                        options={[
                            {
                                label:'Next',
                                action: this.getUnverifiedAnnotation,
                            }
                        ]}
                    />
                );
                imageArea = (
                    <div></div>
                );
            }
        }

        return (
            <div>
                {topBox}
                <div className={'leftbox'}>
                    {imageArea}
                </div>
                <ObjectTable
                    object={this.state.annotation}
                    className={'rightbox'}
                />
            </div>
        );
    }
}

export default AnnotationViewer;
