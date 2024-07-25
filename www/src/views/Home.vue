<script setup>
import TopicButtons from '../components/TopicButtons.vue'
import TopScoresTable from '../components/TopScoresTable.vue';
</script>

<template>
    <nav class="navbar navbar-dark bg-dark text-center text-white fixed-top">
        <div></div>
        <div class="text-center">
            <h1>GenAI Trivia Game</h1>
        </div>
        <div></div>
    </nav>
    <div class="gap-2 col-10 mx-auto mt-5">
        <img id="robot" src="../assets/happy_robot.jpg" class="float-start" width="40%" />
        <div><br><br></div>
        <div class="card mb-4">
            <div class="card-body" ref="transitionMessage"></div>
        </div>
        <div></div>
        <div></div>
        <div class="">
            <h2 class="mb-3">Topics</h2>
            <TopicButtons v-for="topic in topics" v-bind:topic="topic" />
            </br>
            <div ref="categoryContainer" class="mt-2">
                <input type="text" ref="customCategory" placeholder="Enter your own topic" class="ms-2">
                <button @click="submit" id="submit-button" class="btn btn-dark ms-2">Submit</button>
            </div>
        </div>
        <div class="">
            <br />
            <button @click="showScoreTable = !showScoreTable" id="get_top_scores" class="btn btn-dark ms-2"><span
                    v-if="showScoreTable">Hide</span><span v-else>Show</span> Top {{ data.highscores.numberOfHighScores
                }}
                Scores</button>
            <div>
                <TopScoresTable v-if="showScoreTable" :highScores="highScores"></TopScoresTable>
            </div>
        </div>
    </div>
</template>

<script>
import { DynamoDBClient, QueryCommand } from "@aws-sdk/client-dynamodb";
import { fetchAuthSession } from "aws-amplify/auth";
import data from '../data.json'

export default {
    data() {
        return {
            region: data.region,
            topics: data.topics,
            highScores: [],
            showScoreTable: false
        }
    },
    mounted() {
        this.dynamoClient = new DynamoDBClient({ region: this.region, credentials: this.getCreds() });
        async function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        };
        async function updateMessage(messageElement) {
            let message = "Hi! My name is Claude. I am an artificial intelligence that lives in the cloud. Want to test your knowledge against mine? You can select a topic below, or enter your own.. ";
            for (let i = 0; i < message.length; i++) {
                messageElement.insertAdjacentHTML('beforeend', message.charAt(i));
                await sleep(5);
            }
        };
        updateMessage(this.$refs.transitionMessage);
        this.fetchTopScores();
    },
    methods: {
        async getCreds() {
            const session = await fetchAuthSession();
            return session.credentials;
        },
        sanitizeInput(input) {
            // Remove leading and trailing whitespaces
            const trimmedInput = input.trim();

            // Limit the length of the input to a reasonable size
            const maxLength = 50; // Adjust this based on your requirements
            const truncatedInput = trimmedInput.slice(0, maxLength);

            // Escape HTML characters to prevent XSS attacks
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#x27;',
                "/": '&#x2F;',
            };
            const reg = /[&<>"'/]/ig;
            return truncatedInput.replace(reg, (match) => (map[match]));
        },
        submit() {
            this.$router.push({ name: 'Trivia Game', params: { topic: this.sanitizeInput(this.$refs.customCategory.value) } });
        },
        async fetchTopScores() {
            try {
                console.log('getting high scores')
                const highScoresQuery = new QueryCommand({
                    TableName: data.highscores.table,
                    IndexName: data.highscores.scoreIndexName,
                    Limit: data.highscores.numberOfHighScores,
                    ScanIndexForward: false,
                    ExpressionAttributeValues: {
                        ":s": {
                            N: "1"
                        }
                    },
                    KeyConditionExpression: "sortID = :s"
                });
                const response = await this.dynamoClient.send(highScoresQuery);
                this.highScores = response.Items;
            } catch (error) {
                console.error('Error fetching top scores:', error);
            }
        }
    }
}
</script>