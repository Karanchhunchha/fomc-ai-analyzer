% fomc_rag_pipeline.m
% Complete demonstration of a Retrieval-Augmented Generation (RAG) pipeline
% implemented directly in MATLAB.
%
% This script demonstrates:
% 1. Document Extraction & Preprocessing (Text Analytics Toolbox)
% 2. Semantic Chunking & Vector Search (Database Toolbox concept)
% 3. Direct LLM API Integration (Gemini API / OpenRouter via REST)
%
% Part of the MathWorks Excellence in AI Challenge submission (Project #258).

disp('=== Standalone MATLAB RAG Pipeline ===');

%% 1. Document Ingestion & Extraction (Text Analytics Toolbox)
pdfFile = fullfile(pwd, '..', 'data', 'raw', 'fomcminutes20241218.pdf');
if isfile(pdfFile)
    disp(['Extracting text from: ', pdfFile]);
    rawText = extractFileText(pdfFile);
else
    disp('Target PDF not found in data/raw. Using built-in sample transcript corpus...');
    rawText = ["The Committee decided to maintain the target range for the federal funds rate at 5-1/4 to 5-1/2 percent. " ...
               "Inflation has eased over the past year but remains somewhat elevated. " ...
               "The Committee seeks to achieve maximum employment and inflation at the rate of 2 percent over the longer run. " ...
               "In light of the cumulative tightening of monetary policy, the Committee will continue to reduce its holdings of Treasury securities." ...
               "The U.S. banking system is sound and resilient. Tighter financial and credit conditions for households and businesses are likely to weigh on economic activity." ...
               "Geopolitical tensions remain high and represent a source of economic uncertainty."];
    rawText = join(rawText, ' ');
end

% Preprocess into sentences
disp('Chunking text into sentences...');
sentences = splitSentences(rawText);
sentences = string(sentences);
sentences(strlength(sentences) < 15) = []; % Filter out short page numbers/headers
disp(['Total valid text chunks extracted: ', num2str(length(sentences))]);

%% 2. Text Preprocessing & Search (Text Analytics Toolbox)
userQuery = "What did the committee decide regarding interest rates?";
disp(['User Query: "', userQuery, '"']);

% Compute TF-IDF representation for keyword matching (simulating simple search retrieval)
documents = tokenizedDocument(sentences);
documents = removeStopWords(documents);
bag = bagOfWords(documents);
tfidf_matrix = tfidf(bag);

% Preprocess the query
queryDoc = tokenizedDocument(userQuery);
queryDoc = removeStopWords(queryDoc);
queryBag = bagOfWords(queryDoc);

% Search matching indices (Cosine Similarity of TF-IDF vectors)
queryVector = full(encode(queryBag, bag));
corpusVectors = full(tfidf_matrix);

scores = zeros(length(sentences), 1);
for i = 1:length(sentences)
    v = corpusVectors(i, :);
    if norm(v) > 0 && norm(queryVector) > 0
        scores(i) = dot(v, queryVector) / (norm(v) * norm(queryVector));
    end
end

% Retrieve Top 3 matching sentences
[sortedScores, idx] = sort(scores, 'descend');
retrievedChunks = "";
disp('--- Retrieved Evidence Chunks ---');
for k = 1:min(3, length(idx))
    if sortedScores(k) > 0
        retrievedChunks = retrievedChunks + sprintf("Excerpt %d (Score: %.2f):\n%s\n\n", k, sortedScores(k), sentences(idx(k)));
        fprintf('Match %d [Score: %.2f]: %s\n', k, sortedScores(k), sentences(idx(k)));
    end
end

if strlength(retrievedChunks) == 0
    disp('No matching chunks found above threshold. Using top sentence as fallback.');
    retrievedChunks = sprintf("Excerpt 1:\n%s\n", sentences(1));
end

%% 3. Prompt Construction & LLM Generation (REST API call)
disp('Constructing prompt...');
prompt = sprintf([...
    'You are "CK MATLAB Intelligence" — a financial research assistant.\n' ...
    'Answer the USER QUESTION using ONLY the facts present in the CONTEXT EXCERPTS.\n' ...
    'If the excerpts do not contain the answer, reply: "Context does not contain enough evidence."\n\n' ...
    'CONTEXT EXCERPTS:\n%s\n' ...
    'USER QUESTION:\n%s\n\n' ...
    'ANSWER:'], retrievedChunks, userQuery);

% Configure API Key and Endpoint
% Reads the GEMINI_API_KEY environment variable, or falls back to prompt input
apiKey = getenv('GEMINI_API_KEY');
if isempty(apiKey)
    disp('⚠️ GEMINI_API_KEY environment variable is not set.');
    apiKey = input('Please enter your Gemini API Key (or press enter to skip LLM generation): ', 's');
end

if isempty(apiKey)
    disp('Skipping API generation. Prompt generated successfully:');
    disp(prompt);
else
    disp('Connecting to Gemini API...');
    % Configure API details for Gemini 1.5 Flash
    url = ['https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=', apiKey];
    
    % Request body format required by Gemini API
    requestBody = struct('contents', struct('parts', struct('text', prompt)));
    options = weboptions('MediaType', 'application/json', 'Timeout', 30);
    
    try
        response = webwrite(url, requestBody, options);
        
        % Parse Gemini API response structure
        answerText = response.candidates(1).content.parts(1).text;
        disp('=== Grounded LLM Response ===');
        disp(answerText);
    catch apiError
        disp('❌ API Error occurred during LLM generation:');
        disp(apiError.message);
    end
end
disp('RAG Pipeline script execution completed.');
