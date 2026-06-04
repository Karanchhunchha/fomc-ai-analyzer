% fomc_retrieval.m
% Connects to the local FastAPI Python microservice to retrieve RAG answers
% and display them in the MATLAB command window.
%
% Part of the MathWorks Excellence in AI Challenge submission (Project #258).

disp('=== FOMC Microservice Retrieval (MATLAB) ===');

% Define the FastAPI backend query endpoint
apiUrl = 'http://localhost:8000/query';

% Set up query payload
userQuery = 'What did the committee say about inflation and rate cuts?';
fprintf('User Query: "%s"\n', userQuery);

payload = struct('query', userQuery, 'top_k', 3, 'mode', 'auto');
options = weboptions('MediaType', 'application/json', 'Timeout', 30);

try
    disp('Sending request to local FastAPI backend...');
    % Query backend
    response = webwrite(apiUrl, payload, options);
    
    disp('--- Grounded Answer Received ---');
    if isstruct(response) && isfield(response, 'answer')
        disp(response.answer);
    else
        % Print raw payload string if streamed/text format
        disp(char(response));
    end
    
catch ME
    disp('⚠️ FastAPI backend not detected on port 8000.');
    disp('Ensure the backend is running by executing: python -m uvicorn backend.api:app');
    disp(['Error context: ', ME.message]);
    
    % Display simulated fallback for demo completeness
    disp('--- Fallback Demonstration (Simulated Response) ---');
    disp('Answer: Inflation remains elevated but has eased over the past year. ');
    disp('The Committee seeks to return inflation to its 2 percent objective before adjusting interest rates.');
    disp('Confidence Score: 0.89');
end
disp('Retrieval script execution complete.');
