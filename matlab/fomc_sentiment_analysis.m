% fomc_sentiment_analysis.m
% Analyzes monetary policy tone and inflation tracking from FOMC transcripts
% using term frequency analysis.
%
% This script demonstrates:
% 1. Custom domain-specific dictionaries (Hawkish vs Dovish word mapping)
% 2. Term frequency plotting and visualizations (Statistics Toolbox)
% 3. Hawk-Dove Index calculation over the text corpus.
%
% Part of the MathWorks Excellence in AI Challenge submission (Project #258).

disp('=== FOMC Hawkish vs Dovish Sentiment Analysis ===');

%% 1. Sample text / Ingestion
pdfFile = fullfile(pwd, '..', 'data', 'raw', 'fomcminutes20241218.pdf');
if isfile(pdfFile)
    textData = extractFileText(pdfFile);
else
    textData = [...
        "The Committee remains highly attentive to inflation risks. " ...
        "Additional policy firming may be appropriate to return inflation to 2 percent. " ...
        "Economic growth has slowed, but the labor market remains tight with strong job gains. " ...
        "We discuss rate cuts, but restrictive policy must be maintained for some time. " ...
        "Members expressed concern about inflation persistence and upside risks. " ...
        "The Fed will reduce its holdings of Treasury securities and agency debt."];
    textData = join(textData, ' ');
end

%% 2. Word tokenization & Cleaning (Text Analytics Toolbox)
cleanText = lower(textData);
cleanText = erasePunctuation(cleanText);
doc = tokenizedDocument(cleanText);
words = doc.Vocabulary;

%% 3. Domain Dictionary Definition
% Hawkish terms suggest tightening, fighting inflation, keeping rates high
hawkishTerms = ["tighten", "tightening", "firming", "restrictive", "inflation", ...
                "persistence", "upside", "elevated", "firm", "risks", "attentive", "holding"];
            
% Dovish terms suggest easing, accommodation, cutting rates, supporting growth
dovishTerms = ["ease", "easing", "accommodation", "accommodative", "cut", ...
               "cuts", "slowing", "weigh", "downside", "support", "moderate", "easing"];

%% 4. Sentiment Index Computation
hawkishCount = 0;
dovishCount = 0;

hawkishFound = struct();
dovishFound = struct();

% Count frequencies
for i = 1:length(words)
    w = words(i);
    if any(hawkishTerms == w)
        hawkishCount = hawkishCount + 1;
        if isfield(hawkishFound, char(w))
            hawkishFound.(char(w)) = hawkishFound.(char(w)) + 1;
        else
            hawkishFound.(char(w)) = 1;
        end
    elseif any(dovishTerms == w)
        dovishCount = dovishCount + 1;
        if isfield(dovishFound, char(w))
            dovishFound.(char(w)) = dovishFound.(char(w)) + 1;
        else
            dovishFound.(char(w)) = 1;
        end
    end
end

totalHits = hawkishCount + dovishCount;
if totalHits > 0
    % Hawk-Dove Index ranges from -1 (Extremely Dovish) to +1 (Extremely Hawkish)
    sentimentIndex = (hawkishCount - dovishCount) / totalHits;
else
    sentimentIndex = 0;
end

fprintf('\nHawkish Tokens Found: %d\n', hawkishCount);
fprintf('Dovish Tokens Found: %d\n', dovishCount);
fprintf('Computed Hawk-Dove Sentiment Index: %.2f\n', sentimentIndex);

if sentimentIndex > 0.15
    disp('Classification: HAWKISH POLICY TONE 🦅');
elseif sentimentIndex < -0.15
    disp('Classification: DOVISH POLICY TONE 🕊️');
else
    disp('Classification: NEUTRAL/BALANCED POLICY TONE ⚖️');
end

%% 5. Plotting Frequencies (Statistics and Machine Learning Toolbox)
figure('Name', 'FOMC Sentiment Analysis Output');

% Subplot 1: Hawk vs Dove Count
subplot(1, 2, 1);
bar([hawkishCount, dovishCount], 'FaceColor', [0.15, 0.45, 0.75]);
set(gca, 'XTickLabel', {'Hawkish Words', 'Dovish Words'});
ylabel('Occurrences');
title('Macroeconomic Tone Comparison');
grid on;

% Subplot 2: Sentiment Gauge Representation
subplot(1, 2, 2);
theta = linspace(pi, 0, 100);
x = cos(theta);
y = sin(theta);
plot(x, y, 'k-', 'LineWidth', 2);
hold on;
% Draw gauge regions
fill([-1, -0.3, -0.3, -1], [0, 0, 0.3, 0], 'g', 'FaceAlpha', 0.3); % Dovish
fill([-0.3, 0.3, 0.3, -0.3], [0, 0, 0.3, 0], 'y', 'FaceAlpha', 0.3); % Neutral
fill([0.3, 1, 1, 0.3], [0, 0, 0.3, 0], 'r', 'FaceAlpha', 0.3); % Hawkish

% Draw indicator needle based on sentimentIndex
needle_angle = pi - (sentimentIndex + 1) * (pi/2);
plot([0, cos(needle_angle)*0.8], [0, sin(needle_angle)*0.8], 'r-', 'LineWidth', 4);
xlim([-1.2, 1.2]);
ylim([-0.1, 1.1]);
title(sprintf('Hawk-Dove Index: %.2f', sentimentIndex));
text(-0.9, 0.1, 'Dovish', 'FontSize', 12);
text(-0.15, 0.8, 'Neutral', 'FontSize', 12);
text(0.6, 0.1, 'Hawkish', 'FontSize', 12);
axis off;
hold off;

disp('Sentiment metrics generated successfully.');
