import React from 'react';

class ImageCanvas extends React.Component{
    constructor(props){
        super(props);
        this.canvasRef = React.createRef();
        this.state = {
            imageSrc: '',
            drawingEnabled: false,
            drawingActive: false,
            boxes: []
        };

        this.canvasOnClick = this.canvasOnClick.bind(this);
        this.drawBox = this.drawBox.bind(this);
        this.drawCanvas = this.drawCanvas.bind(this);
        this.clearCanvas = this.clearCanvas.bind(this);
        this.cancelDrawing = this.cancelDrawing.bind(this);
        this.prepareImage = this.prepareImage.bind(this);
        this.canvasOnMouseMove = this.canvasOnMouseMove.bind(this);
        this.createBox = this.createBox.bind(this);
    }

    componentDidMount(){
        this.setState(
        {
            imageSrc: this.props.imageSrc,
            imageLoaded: false
        },
        () => {
            this.prepareImage();
        });
    }

    componentDidUpdate(prevProps, prevState){
    if(this.canvasRef && this.canvasRef.current){
        this.canvasRef.current.style.cursor = 'crosshair';   
    }        
    if(prevState.drawingEnabled !== this.props.drawingEnabled){
            this.setState({
                drawingEnabled: this.props.drawingEnabled
            });
        }
        // handle case where drawing was cleared in the middle of drawing a box
        if(prevProps.boxes.length > 0 && this.props.boxes.length == 0){
            this.cancelDrawing();
        }
        
        if(prevState.imageSrc !== this.props.imageSrc){
            this.clearCanvas();
            this.setState(
                {
                    imageSrc: this.props.imageSrc,
                    imageLoaded: false
                },
                () => {
                    this.prepareImage();
                });
        }
        else{
            this.drawCanvas();
        }
    }

    prepareImage(){
        let image = new Image();
        image.onload = ()=>{
            let context = this.canvasRef && this.canvasRef.current ? this.canvasRef.current.getContext('2d') : null;
            if(context){
                const canvas = this.canvasRef.current;
                let origWidth = image.width;
                let origHeight = image.height;

                let canvasWidth = canvas.width;
                let canvasHeight = canvas.height;

                let ratio = origWidth > canvasWidth ? canvasWidth/origWidth : origWidth/canvasWidth;
                let newWidth = origWidth * ratio;
                let newHeight = origHeight * ratio;
                if(newHeight > canvasHeight){
                    ratio = origHeight > canvasHeight ? canvasHeight/origHeight : origHeight/canvasHeight;
                    newHeight = origHeight * ratio;
                    newWidth = origWidth * ratio;
                }
            
                let wOffset = (canvasWidth - newWidth)/2;
                let hOffset = (canvasHeight - newHeight)/2;

                this.setState({
                      imageLoaded: true,
                      scaleRatio: ratio,
                      wOffset: wOffset,
                      hOffset: hOffset,
                      scaledWidth: newWidth,
                      scaledHeight: newHeight,
                    },
                    () => {
                       this.drawCanvas();
                    }
                );
            }
        }
        image.src = this.state.imageSrc;
    }

    clearCanvas(){
        let context = this.canvasRef && this.canvasRef.current ? this.canvasRef.current.getContext('2d') : null;
        if(context){
            const canvas = this.canvasRef.current;
            context.clearRect(0, 0, canvas.width, canvas.height);
        }
    }

    drawCanvas(){
        if(!this.state.imageLoaded){
            return;
        }

        if(!this.state.imageObj){
            let image = new Image();
            image.onload = ()=>{
                this.setState({imageObj: image}, () => { this.drawCanvas() });
            }
            image.src = this.state.imageSrc; 
        }        
        else{
            const image = this.state.imageObj;
            let context = this.canvasRef && this.canvasRef.current ? this.canvasRef.current.getContext('2d') : null;
            if(context){
                const canvas = this.canvasRef.current;
                context.clearRect(0, 0, canvas.width, canvas.height);
                context.drawImage(image, 
                                    0,
                                    0,
                                    image.width,
                                    image.height, 
                                    this.state.wOffset, 
                                    this.state.hOffset, 
                                    this.state.scaledWidth, 
                                    this.state.scaledHeight);
                this.props.boxes.forEach((box) => {
                    this.drawBox(box);
                });
            }          
        };
    }

    drawBox(box, shouldScale=true){
        let canvas = this.canvasRef.current; 
        let context = canvas.getContext('2d');
        const ratio = shouldScale ? (this.state.scaleRatio || 1.0) : 1.0;

        context.fillStyle = box.color || 'green';
        context.globalAlpha = 0.35;
        context.fillRect(box.x0*ratio,
                         box.y0*ratio, 
                         (box.x1-box.x0)*ratio, 
                         (box.y1-box.y0)*ratio
        );
        context.globalAlpha = 1.0;
    }

    cancelDrawing(){
        this.setState({ drawingActive:false });
        /*if(this.canvasRef.current){
            this.canvasRef.current.style.cursor = 'default';
        }*/
    }

    beginDrawing(){
        this.setState({ drawingActive:true });
        /*if(this.canvasRef.current){
            this.canvasRef.current.style.cursor = 'crosshair';   
        }*/
    }

    canvasOnClick(evt, boxHandler){
        if(this.state.drawingEnabled){
            let canvas = this.canvasRef.current;
            if(this.state.drawingActive){
                // ending a rectangle
                let endX = evt.clientX - canvas.getBoundingClientRect().left;
                let endY = evt.clientY - canvas.getBoundingClientRect().top;
                
                if(boxHandler){
                    // don't forget to scale back up...
                    const ratio = this.state.scaleRatio || 1.0;
                    const box = this.createBox(
                            Math.min(this.state.startX, endX),
                            Math.max(this.state.startX, endX),
                            Math.min(this.state.startY, endY),
                            Math.max(this.state.startY, endY)
                    );

                    boxHandler(box.x0, box.x1, box.y0, box.y1);
                }
                this.cancelDrawing();
            }   
            else{
                // beginning a rectangle
                this.beginDrawing();
                let startX = evt.clientX - canvas.getBoundingClientRect().left;
                let startY = evt.clientY - canvas.getBoundingClientRect().top;

                if(startX < this.state.wOffset){
                    startX = this.state.wOffset;
                }
                else if(startX > this.state.wOffset + this.state.scaledWidth){
                    startX = this.state.wOffset + this.state.scaledWidth;
                }

                if(startY < this.state.hOffset){
                    startY = this.state.hOffset;
                }
                else if(startY > this.state.hOffset + this.state.scaledHeight){
                    startY = this.state.hOffset + this.state.scaledHeight;
                }
               
                this.setState({
                    startX: startX,
                    startY: startY,
                });                
            }
        }
    }

    createBox(startX, endX, startY, endY, color, shouldScale=true){
        // don't forget to scale back up...
        const ratio = shouldScale ? (this.state.scaleRatio || 1.0) : 1.0;
        const box = {
            x0: startX/ratio,
            x1: endX/ratio,
            y0: startY/ratio,
            y1: endY/ratio,
            color: color || 'green',
        };

        return box;
    }

    canvasOnMouseMove(evt){
        this.clearCanvas();
        this.drawCanvas();
        if(this.state.drawingActive){
            let canvas = this.canvasRef.current;
            let currX = evt.clientX - canvas.getBoundingClientRect().left;
            let currY = evt.clientY - canvas.getBoundingClientRect().top;

            const box = this.createBox(
                Math.min(currX, this.state.startX),
                Math.max(currX, this.state.startX),
                Math.min(currY, this.state.startY),
                Math.max(currY, this.state.startY),
                'red',
                false);

            this.drawBox(box, false);
        }
    }

    render(){
        return (
            <canvas 
                ref={this.canvasRef} 
                width="768"
                height="432"
                style={{height:'432px', width:'768px'}} 
                onClick={(evt) => {
                    this.canvasOnClick(evt, this.props.boxHandler);
                }}
                onMouseMove={(evt)=>{
                    this.canvasOnMouseMove(evt);
                }}
            />
        );
    }

}

export default ImageCanvas;
