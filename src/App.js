import React, { useState } from 'react';
import './App.css';

const steps = [
    {
        title: "Preparation of Phenylacetone",
        uploadFields: [
            "Phenylacetone weight",
            "Ethanol volume",
            "Reflux temperature",
            "Reflux time"
        ]
    },
    {
        title: "Reaction with Hydroxylamine",
        uploadFields: [
            "Hydroxylamine weight",
            "Addition time",
            "Stirring temperature",
            "Stirring time"
        ]
    },
    {
        title: "Cyclization Reaction",
        uploadFields: [
            "Acetic acid volume",
            "Sulfuric acid volume",
            "Reflux temperature",
            "Reflux time"
        ]
    },
    {
        title: "Purification of Paracetamol",
        uploadFields: [
            "Vacuum distillation pressure",
            "Crystallization solvent",
            "Crystallization temperature"
        ]
    }
];

const MAX_FILE_SIZE_MB = 5; // Maximum file size in MB
const ALLOWED_FILE_TYPES = ["image/jpeg", "image/png", "image/jpg"];

const DrugPreparationProcess = () => {
    const [currentStep, setCurrentStep] = useState(0);
    const [files, setFiles] = useState({});
    const [errorMessages, setErrorMessages] = useState({});
    const [successMessages, setSuccessMessages] = useState({});
    const [validationMessages, setValidationMessages] = useState({});

    const handleFileChange = (event, field) => {
        const file = event.target.files[0];

        // Reset previous messages for this field
        setErrorMessages({ ...errorMessages, [field]: null });
        setSuccessMessages({ ...successMessages, [field]: null });
        setValidationMessages({ ...validationMessages, [field]: null });

        if (!file) {
            setErrorMessages({ ...errorMessages, [field]: "No file selected." });
            return;
        }

        // Check file size
        if (file.size / 1024 / 1024 > MAX_FILE_SIZE_MB) {
            setErrorMessages({ ...errorMessages, [field]: `File size exceeds ${MAX_FILE_SIZE_MB} MB.` });
            return;
        }

        // Check file type
        if (!ALLOWED_FILE_TYPES.includes(file.type)) {
            setErrorMessages({ ...errorMessages, [field]: "Unsupported file type. Please upload a JPEG or PNG image." });
            return;
        }

        // If all checks pass, update the state
        setFiles({
            ...files,
            [field]: file,
        });
        setSuccessMessages({ ...successMessages, [field]: `File for ${field} uploaded successfully.` });
    };

    const handleValidation = async () => {
        // Check if required files are uploaded and validate them
        const requiredFields = steps[currentStep].uploadFields;

        const validationResults = await Promise.all(requiredFields.map(async (field) => {
            if (!files[field]) {
                setErrorMessages(prev => ({ ...prev, [field]: "No file uploaded. Validation cannot be performed." }));
                return false;
            }

            const formData = new FormData();
            formData.append("step_number", currentStep + 1);
            formData.append("variable", field);
            formData.append("file", files[field]);

            try {
                const response = await fetch("http://localhost:5000/validate", {
                    method: "POST",
                    body: formData,
                });
                const result = await response.json();
                if (response.ok) {
                    if (!result.valid) {
                        setValidationMessages(prev => ({
                            ...prev,
                            [field]: `Validation failed for ${field}.`
                        }));
                        return false;
                    } else {
                        setSuccessMessages(prev => ({
                            ...prev,
                            [field]: `Validated: ${result.measurement} ${result.units}`
                        }));
                        return true;
                    }
                } else {
                    setValidationMessages(prev => ({
                        ...prev,
                        [field]: `Server error: ${result.error}. Validation failed.`
                    }));
                    return false;
                }
            } catch (error) {
                setValidationMessages(prev => ({
                    ...prev,
                    [field]: `Error during validation.`
                }));
                return false;
            }
        }));

        return validationResults.includes(false) ? false : true;
    };

    const handleProceed = () => {
        // Proceed to the next step
        setCurrentStep(currentStep + 1);
    };

    const progress = ((currentStep + 1) / steps.length) * 100;

    return (
        <div className="container">
            <h1>Drug Preparation Process</h1>

            <div className="progress-bar">
                <div
                    className="progress-bar-inner"
                    style={{ width: `${progress}%` }}
                ></div>
            </div>

            <h2>{steps[currentStep].title}</h2>
            <form>
                {steps[currentStep].uploadFields.map((field, index) => (
                    <div className="file-upload" key={index}>
                        <label>Upload image for {field}:</label>
                        <input
                            type="file"
                            onChange={(e) => handleFileChange(e, field)}
                            accept=".jpg,.png,.jpeg"
                        />
                        {errorMessages[field] && <div className="error-message">{errorMessages[field]}</div>}
                        {successMessages[field] && <div className="success-message">{successMessages[field]}</div>}
                        {validationMessages[field] && <div className="error-message">{validationMessages[field]}</div>}
                    </div>
                ))}
                <div className="button-group">
                    <button type="button" onClick={handleValidation}>
                        <i className="fas fa-check-circle"></i> Validate
                    </button>
                    <button type="button" onClick={handleProceed}>
                        <i className="fas fa-arrow-right"></i> Proceed to Next Step
                    </button>
                </div>
            </form>

            {currentStep === steps.length && (
                <div className="success-message">All steps completed successfully!</div>
            )}
        </div>
    );
};

export default DrugPreparationProcess;
