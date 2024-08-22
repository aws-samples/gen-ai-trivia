<template>
    <div>
        <div ref="loadingArea" class="text-center mt-5">
            <h3>Loading the next question...</h3>
            <div class="spinner-border text-success" role="status">
                <span class="sr-only"></span>
            </div>
        </div>
        <div ref="content" class="mt-5">
            <div class="progress">
                <div ref="progressBar" class="progress-bar bg-success" role="progressbar" style="width: 100%"
                    aria-valuenow="100" aria-valuemin="0" aria-valuemax="100">{{ timer }} seconds</div>
            </div>
            <div class="text-center mt-5">
                <div class="card">
                    <div class="card-header p-5" id="question" ref="questionText">{{
                        currentQuestionText }}</div>

                    <div class="card-body">
                        <div class="row mb-3">

                            <div class="col-md-4"></div>
                            <div class="col-md-4 border border-secondary rounded p-3" disabled id="up" ref="up"
                                @click="handleClick($event, answer1)">{{
                                    answer1
                                }}
                            </div>

                            <div class="col-md-4"></div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-md-1"></div>
                            <div class="col-md-4 border border-secondary rounded p-3" id="left" ref="left"
                                @click="handleClick($event, answer2)">{{
                                    answer2
                                }}
                            </div>
                            <div class="col-md-2"></div>
                            <div class="col-md-4 border border-secondary rounded p-3" id="right" ref="right"
                                @click="handleClick($event, answer3)">{{
                                    answer3
                                }}</div>
                            <div class="col-md-1"></div>
                        </div>
                        <div class="row mb-5">
                            <div class="col-md-4"></div>
                            <div class="col-md-4 border border-secondary rounded p-3" id="down" ref="down"
                                @click="handleClick($event, answer4)">{{
                                    answer4
                                }}
                            </div>
                            <div class="col-md-4"></div>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { LambdaClient, InvokeWithResponseStreamCommand } from "@aws-sdk/client-lambda";
import { fetchAuthSession } from 'aws-amplify/auth';
import data from '../data.json'

export default {
    props: ['topic', 'roundNumber', 'previousQuestions'],
    emits: ["increase-score", "next-round", "set-previous-questions-list", "update-accuracy"],
    data() {
        return {
            questions: [],
            currentQuestion: 0,
            difficulty: data.rounds[this.roundNumber - 1].difficulty,
            region: data.region,
            functionName: data.bedrockFunctionName,
            number_of_questions: data.rounds[this.roundNumber - 1].numberOfQuestions,
            answer1: '',
            answer2: '',
            answer3: '',
            answer4: '',
            currentQuestionText: '',
            timer: 60,
            startTime: 60,
            betweenQuestions: false
        }
    },
    methods: {
        async handleClick(e, answer) {
            if (this.betweenQuestions) {
                return
            }
            const element = e.target;
            this.checkAnswer(element, answer);
        },
        handleKeyup(event) {
            if (this.betweenQuestions) {
                return
            }
            let element;
            let answer;
            switch (event.code) {
                case "ArrowUp":
                    element = this.$refs.up;
                    answer = this.answer1;
                    break
                case "ArrowDown":
                    element = this.$refs.down;
                    answer = this.answer4;
                    break
                case "ArrowLeft":
                    element = this.$refs.left;
                    answer = this.answer2;
                    break
                case "ArrowRight":
                    element = this.$refs.right;
                    answer = this.answer3;
                    break
                default:
                    return
            }
            if (element && answer) {
                this.checkAnswer(element, answer);
            }
        },
        async checkAnswer(element, answer) {
            this.betweenQuestions = true;
            const correctAnswer = this.questions[this.currentQuestion].correctAnswer;
            const allAnswers = this.questions[this.currentQuestion].answers;
            let correctElement;
            if (answer === correctAnswer) {
                element.classList.add('bg-success');
                this.$emit('update-accuracy', true);
                this.updateScore();
            } else {
                this.$emit('update-accuracy', false);
                const correctIndex = allAnswers.indexOf(correctAnswer);
                element.classList.add('bg-danger');
                switch (parseInt(correctIndex)) {
                    case 0:
                        correctElement = this.$refs.up;
                        break;
                    case 1:
                        correctElement = this.$refs.left;
                        break;
                    case 2:
                        correctElement = this.$refs.right;
                        break;
                    case 3:
                        correctElement = this.$refs.down;
                        break;
                }
                correctElement.classList.add('text-warning');
                correctElement.classList.add('font-weight-bold');
                correctElement.classList.add('border-warning');
                correctElement.classList.add('bg-success');
            }
            // Clear the colors after a delay
            const _this = this;
            await setTimeout(function () { // nosemgrep: detect-eval-with-expression
                element.classList.remove('bg-success', 'bg-danger');
                if (correctElement) {
                    correctElement.classList.remove('text-warning');
                    correctElement.classList.remove('font-weight-bold');
                    correctElement.classList.remove('border-warning');
                    correctElement.classList.remove('bg-success');
                }
                _this.currentQuestion += 1;
                if (_this.currentQuestion < _this.number_of_questions) {
                    _this.showNextQuestion();
                    _this.betweenQuestions = false;
                } else {
                    _this.$emit('set-previous-questions-list', _this.questions);
                    _this.$emit('next-round');
                }
            }, 1000, _this);
            this.startTime = this.timer;
        },
        showNextQuestion() {
            if (this.questions[this.currentQuestion] == undefined || !this.questions[this.currentQuestion]) {
                this.$refs.content.style.display = "none";
                this.$refs.loadingArea.style.display = "block";
                const _this = this;
                setTimeout(function () {
                    _this.showNextQuestion();
                }, 500, _this);
            } else {
                this.$refs.loadingArea.style.display = "none";
                this.$refs.content.style.display = "block";
                this.betweenQuestions = false;
                console.log(this.questions[this.currentQuestion]);
                this.currentQuestionText = this.questions[this.currentQuestion].question;
                let answers = this.questions[this.currentQuestion].answers.sort(() => Math.random() - 0.5);
                this.answer1 = answers[0];
                this.answer2 = answers[1];
                this.answer3 = answers[2];
                this.answer4 = answers[3];
            }
        },
        updateScore() {
            let points = 0;
            const duration = this.startTime - this.timer
            if (duration <= 2) {
                points = 300;
            } else if (duration <= 3) {
                points = 200;
            } else {
                points = 100;
            }
            this.$emit('increase-score', points);
        }
    },
    mounted() {
        this.$refs.content.style.display = "none";
        window.addEventListener('keyup', this.handleKeyup);
        async function getQuestions(_this) {
            let count = 1;
            const session = await fetchAuthSession();
            const client = new LambdaClient({ region: _this.region, credentials: session.credentials });
            const input = { // InvokeWithResponsestreamRequest
                FunctionName: _this.functionName,
                Payload: JSON.stringify({
                    number_questions: _this.number_of_questions,
                    difficulty: _this.difficulty,
                    topic: _this.topic,
                    num_silly: 'one',
                    existing_questions: _this.previousQuestions
                })
            };
            const command = new InvokeWithResponseStreamCommand(input);
            const response = await client.send(command);
            const decoder = new TextDecoder('utf-8')
            let questionsstring = '';
            for await (const chunk of response.EventStream) {
                let decodedChunk = decoder.decode(chunk.PayloadChunk?.Payload);
                if (decodedChunk.includes('}')) {
                    let nextQuestionChunk
                    if (decodedChunk.length > 1 && decodedChunk != '},' && decodedChunk != '}, ') {
                        let splitChunk = decodedChunk.split('}');
                        let questionEndChunk = splitChunk[0] + '}';
                        nextQuestionChunk = splitChunk[1].replace(',{', '{');
                        questionsstring = questionsstring + questionEndChunk;
                    } else {
                        questionsstring += decodedChunk.replace(',', '').replace(' ', '');
                        nextQuestionChunk = '';
                    }
                    if (questionsstring.indexOf('[') == 0) {
                        questionsstring = questionsstring.replace('[', '');
                    }
                    if (questionsstring.indexOf(',') == 0) {
                        questionsstring = questionsstring.replace(',', '');
                    }
                    let parsedQuestion;
                    try {
                        parsedQuestion = JSON.parse(questionsstring);
                    } catch (e) {
                        console.error("Error parsing question:");
                        console.error(questionsstring);
                        console.error(e);
                    }
                    _this.questions.push(parsedQuestion);
                    count++;
                    if (_this.questions.length == 1) {
                        _this.$refs.content.style.display = "block";
                        _this.$refs.loadingArea.style.display = "none";
                        _this.answer1 = _this.questions[0].answers[0];
                        _this.answer2 = _this.questions[0].answers[1];
                        _this.answer3 = _this.questions[0].answers[2];
                        _this.answer4 = _this.questions[0].answers[3];
                        _this.currentQuestionText = _this.questions[0].question;
                    }
                    if (_this.questions.length == _this.number_of_questions) {
                        break;
                    }
                    questionsstring = nextQuestionChunk;
                } else {
                    questionsstring = questionsstring + decodedChunk;
                }
            }
        }
        getQuestions(this);
        const _this = this;
        let coundivown = setInterval(function () {
            if (_this.questions.length > 0 && _this.questions.length >= _this.currentQuestion) {
                _this.timer--;
                if (_this.$refs.progressBar != null && _this.$refs.progressBar) {
                    _this.$refs.progressBar.style.width = (_this.timer / 60) * 100 + "%";

                    if (_this.timer < 16 && _this.timer > 7) {
                        _this.$refs.progressBar.classList.value = 'progress-bar bg-warning';
                    }
                    if (_this.timer < 7) {
                        _this.$refs.progressBar.classList.value = 'progress-bar bg-danger';
                    }
                }
                if (_this.timer <= 0) {
                    _this.$emit('set-previous-questions-list', _this.questions);
                    _this.$emit('next-round');
                }
            }
        }, 1000, _this)
    }
}
</script>
