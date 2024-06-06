// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

const util = require('util');
const stream = require('stream');
const { Readable } = stream;
const pipeline = util.promisify(stream.pipeline);

const {
    BedrockRuntimeClient,
    InvokeModelWithResponseStreamCommand,
} = require('@aws-sdk/client-bedrock-runtime'); // ES Modules import

const bedrock = new BedrockRuntimeClient({ region: 'us-east-1' });

function parseBase64(message) {
    return JSON.parse(Buffer.from(message, 'base64').toString('utf-8'));
}

exports.handler = awslambda.streamifyResponse(
    async (event, responseStream, _context) => {

        console.log('Event: ' + JSON.stringify(event));
        const promptText = `I'm creating a trivia game and need questions and answers generated on the topic of ${event.topic}. Can you generate question and answer pairs using the following rules outlined below?
        <RULES>
           1. Generate ${event.number_questions} ${event.difficulty} questions with each question having four answers, only one of which is correct
           2. ${event.num_silly} of the questions should have one silly answer, but the others should not.
           3. Provide the questions and answers as a JSON array, and indicate which is the correct answer for each question by assigning it a key called correctAnswer. 
           4. Ensure that the correct answer is one of the answers supplied. 
           5. Skip the preamble in the output.
           6. Ensure that there are no questions and answers that have been asked before by comparing them with the previously asked questions supplied.
        </RULES>
        <PREVIOUSLY-ASKED-QUESTIONS>
        ${JSON.stringify(event.existing_questions)}
        </PREVIOUSLY-ASKED-QUESTIONS>`

        const messages = [{ role: 'user', content: promptText }];
        const body = {
            anthropic_version: 'bedrock-2023-05-31',
            max_tokens: 2048,
            temperature: 0.9,
            system: "",
            messages: messages,
        }

        const params = {
            body: JSON.stringify(body),
            contentType: 'application/json',
            modelId: 'anthropic.claude-3-sonnet-20240229-v1:0'
        };

        console.log(params);

        const command = new InvokeModelWithResponseStreamCommand(params);

        const response = await bedrock.send(command);
        console.log('Response: ' + JSON.stringify(response));
        const chunks = [];

        for await (const chunk of response.body) {
            console.debug('CHUNK:');
            console.debug(chunk);
            const parsed = parseBase64(chunk.chunk.bytes);
            console.debug('PARSED:');
            console.debug(parsed);
            if (parsed.type === 'content_block_delta') {
                chunks.push(parsed.delta.text);
                responseStream.write(parsed.delta.text);
            }
        }

        console.log('Stream retreival is complete. Final full response:');
        console.log(chunks.join(''));
        responseStream.end();
    }
);