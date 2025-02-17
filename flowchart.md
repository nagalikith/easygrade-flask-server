```mermaid
flowchart TD
    Start((Start)) --> Input[Student Submissions]
    Input --> Text[Text Answers]
    Input --> Images[Handwritten Images]
    
    Text --> TextPrep[Text Preprocessing]
    TextPrep --> TextVec[Text Vectorization]
    TextVec --> Vectors[Feature Vectors]
    
    Images --> OCR[OCR Processing]
    OCR --> TextPrep
    Images --> ImageVec[Image Feature Extraction]
    ImageVec --> Vectors
    
    Vectors --> DR[Dimensionality Reduction]
    DR --> KM[K-means Clustering]
    
    KM --> G1[Group 1]
    KM --> G2[Group 2]
    KM --> G3[Group 3]
    
    G1 --> Review[Teacher Review Interface]
    G2 --> Review
    G3 --> Review