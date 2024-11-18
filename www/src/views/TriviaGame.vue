<template>
    <nav class="navbar navbar-dark bg-dark text-center text-white fixed-top">
        <span class="display-7 ms-5">{{ topic }} Round {{ roundNumber }}</span>
        <h1 class="text-center display-4">GenAI Trivia Game</h1>
        <div>
            <span class="display-7 me-5" id="score">Score: {{ score }} | Accuracy: {{ accuracyPercent }}%</span>
            <button class="btn btn-outline-danger me-5" type="button" @click="quitGame">Quit</button>
        </div>
    </nav>
    <div>
        <component :is="currentComponent" :topic="topic" :roundNumber="roundNumber" :score="score"
            :accuracy="accuracyPercent" :previousQuestions="previousQuestions" @increase-score="increaseScore"
            @update-accuracy="updateAccuracy" @next-round="nextRound"
            @set-previous-questions-list="setPreviousQuestions" @start-round="startRound">
        </component>
    </div>
</template>

<script>

import RoundTransition from '../components/RoundTransition.vue';
import Questions from '../components/Questions.vue';
import FinalScore from '../components/FinalScore.vue';

export default {
    components: {
        RoundTransition,
        Questions,
        FinalScore
    },
    data() {
        return {
            currentComponent: "RoundTransition",
            roundNumber: 1,
            score: 0,
            accuracy: { numCorrect: 0, numAnswered: 0 },
            accuracyPercent: 0,
            previousQuestions: [],
            roundScore: 0
        }
    },
    props: ['topic'],
    methods: {
        increaseScore(points) {
            this.roundScore += points;
            this.score += points;
        },
        updateAccuracy(wasCorrect) {
            console.log("update accuracy")
            console.log(wasCorrect)
            const correct = wasCorrect ? 1 : 0;
            console.log(correct)
            this.accuracy.numCorrect += correct;
            this.accuracy.numAnswered += 1;
            console.log(this.accuracy)
            this.accuracyPercent = Math.round(this.accuracy.numCorrect / this.accuracy.numAnswered * 100);
            console.log(this.accuracyPercent)
        },
        nextRound() {
            if (this.roundScore < 1000 || this.roundNumber === 3) {
                this.currentComponent = "FinalScore"
            }
            else {
                this.roundNumber += 1;
                this.roundScore = 0;
                this.currentComponent = "RoundTransition";
            }
        },
        startRound() {
            this.currentComponent = "Questions"
        },
        setPreviousQuestions(questionsList) {
            this.previousQuestions.push(...questionsList);
        },
        quitGame() {
            this.$router.push({ path: '/' });
        }
    }
}
</script>