% fomc_downloader.m
% Programmatically downloads FOMC meeting minutes PDFs from the Board of 
% Governors of the Federal Reserve System.
% Uses core MATLAB functions: webread, websave, regexp.
% Part of the MathWorks Excellence in AI Challenge submission (Project #258).

disp('=== FOMC Document Downloader (MATLAB) ===');

% Target folder for raw data
outputFolder = fullfile(pwd, '..', 'data', 'raw');
if ~exist(outputFolder, 'dir')
    mkdir(outputFolder);
    disp(['Created directory: ', outputFolder]);
end

% Federal Reserve FOMC Calendars main landing page
baseUrl = 'https://www.federalreserve.gov';
calendarUrl = [baseUrl, '/monetarypolicy/fomccalendars.htm'];

options = weboptions('Timeout', 20, 'UserAgent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)');

try
    disp('Retrieving FOMC calendars page...');
    html = webread(calendarUrl, options);
    
    % Find recent minutes PDF links in the format: /monetarypolicy/files/fomcminutes20XXXXXX.pdf
    % Match: "/monetarypolicy/files/fomcminutes20\d{6}.pdf"
    pattern = '/monetarypolicy/files/fomcminutes20\d{6}\.pdf';
    matches = unique(regexp(html, pattern, 'match'));
    
    if isempty(matches)
        disp('No PDF minute links found via regex. Attempting fallback download links...');
        % Fallback: Hardcode a few recent/historical minutes files for direct download
        matches = { ...
            '/monetarypolicy/files/fomcminutes20241218.pdf', ... % Dec 2024
            '/monetarypolicy/files/fomcminutes20241107.pdf', ... % Nov 2024
            '/monetarypolicy/files/fomcminutes20240918.pdf'      % Sep 2024
        };
    end
    
    numDownloads = min(3, length(matches)); % Limit to 3 files to save bandwidth/speed
    disp(['Found ', num2str(length(matches)), ' potential PDF links. Downloading top ', num2str(numDownloads), '...']);
    
    for i = 1:numDownloads
        pdfPath = matches{i};
        [~, fileName, fileExt] = fileparts(pdfPath);
        fullName = [fileName, fileExt];
        targetFile = fullfile(outputFolder, fullName);
        
        fullDownloadUrl = [baseUrl, pdfPath];
        disp(['Downloading: ', fullDownloadUrl]);
        
        try
            websave(targetFile, fullDownloadUrl, options);
            disp(['✅ Successfully saved to: ', targetFile]);
        catch downloadError
            disp(['❌ Failed to download ', fullName, ': ', downloadError.message]);
        end
    end
    disp('Downloader execution completed.');
    
catch err
    disp('Failed to connect to Federal Reserve servers.');
    disp(['Error message: ', err.message]);
    
    % Guide user to direct download
    disp('Please manually download minutes from: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm');
    disp(['and place them in: ', outputFolder]);
end
