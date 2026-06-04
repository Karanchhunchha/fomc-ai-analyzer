% ingest_documents.m
% Demonstrates document ingestion and preprocessing using the Text Analytics Toolbox.
%
% This script parses FOMC documents, cleans them, tokenizes, removes stop
% words, and prints statistical highlights.
%
% Part of the MathWorks Excellence in AI Challenge submission (Project #258).

disp('=== Ingesting and Preprocessing FOMC Documents (MATLAB) ===');

% Search for downloaded PDFs in data/raw
rawFolder = fullfile(pwd, '..', 'data', 'raw');
pdfFiles = dir(fullfile(rawFolder, '*.pdf'));

if ~isempty(pdfFiles)
    targetFile = fullfile(rawFolder, pdfFiles(1).name);
    fprintf('Parsing PDF document: %s\n', pdfFiles(1).name);
    try
        textData = extractFileText(targetFile);
    catch extractionError
        disp(['Could not extract text: ', extractionError.message]);
        textData = getSampleText();
    end
else
    disp('No PDF documents found in data/raw. Running with simulated fallback text corpus.');
    textData = getSampleText();
end

% 1. Clean formatting
cleanText = lower(textData);
cleanText = erasePunctuation(cleanText);

% 2. Tokenize and remove stop words (Text Analytics Toolbox)
disp('Tokenizing document contents...');
documents = tokenizedDocument(cleanText);
documents = removeWords(documents, stopWords);

% 3. Extract sentences
sentences = splitSentences(textData);
sentences = string(sentences);

% 4. Print Statistics
fprintf('\n--- Document Token Statistics ---\n');
fprintf('Total original characters: %d\n', strlength(textData));
fprintf('Vocabulary count (unique words): %d\n', length(documents.Vocabulary));
fprintf('Total sentences extracted: %d\n', length(sentences));

disp('First 15 cleaned vocabulary tokens:');
disp(documents.Vocabulary(1:min(15, length(documents.Vocabulary))));

function text = getSampleText()
    text = [...
        "The Federal Open Market Committee decided to maintain the target range for the federal funds rate at 5-1/4 to 5-1/2 percent. " ...
        "Recent indicators suggest that economic activity has been expanding at a solid pace. " ...
        "Job gains have moderated since earlier in the year but remain strong, and the unemployment rate has remained low. " ...
        "Inflation has eased over the past year but remains elevated. " ...
        "The Committee seeks to achieve maximum employment and inflation at the rate of 2 percent over the longer run."];
    text = join(text, ' ');
end
