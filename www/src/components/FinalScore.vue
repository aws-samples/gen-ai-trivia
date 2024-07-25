<script setup>
import TopScoresTable from '../components/TopScoresTable.vue'
</script>
<template>
    <div>
        <h1 class="display-5 text-center mt-5">Game Over</h1>
        <div class="gap-2 mt-5">
            <img id="happy-img" src="../assets/happy_robot_smile_right.jpg" class="float-start" width="30%">
            <div ref="message" class="card p-3 w-50 mt-5">
                <p>You made it through {{ roundNumber }} rounds with a final score of {{ score }} and accuracy of {{
                    accuracy }}%</p>
            </div>
            <div v-if="newHighScore || saveAllScores" class="card mt-3 w-50 border-success">
                <div v-if="newHighScore" class="card-header bg-success text-white">
                    <p>Congrats!! Your score is in the top {{ numberOfHighScores }} highest scores!</p>
                </div>
                <div class="card-body">
                    <p v-if="newHighScore">Recored your score for future players to try to beat it!</p>
                    <p v-else>You didn't crack the top {{ numberOfHighScores }} but record your score anyway to see
                        where you stack up amongst
                        all players!</p>
                    <input type="text" id="highScoreName" v-model="highScoreName" placeholder="Enter your name" />
                    <button class="btn btn-dark ms-2" type="submit" @click="addHighScore">Submit</button>
                </div>
            </div>
            <TopScoresTable v-if="renderTable" :highScores="highScores"></TopScoresTable>
            <div class="position-absolute start-50">
                <button class="btn btn-success btn-lg" @click="restart">Play Again?</button>
            </div>
        </div>
    </div>
</template>

<script>
import { DynamoDBClient, PutItemCommand, QueryCommand } from "@aws-sdk/client-dynamodb";
import { fetchAuthSession } from "aws-amplify/auth";
import data from '../data.json';

export default {
    props: ['topic', 'roundNumber', 'score', 'accuracy'],
    data() {
        return {
            region: data.region,
            highScoreName: '',
            tableName: data.highscores.table,
            scoreIndexName: data.highscores.scoreIndexName,
            numberOfHighScores: data.highscores.numberOfHighScores,
            saveAllScores: data.highscores.saveAllScores,
            newHighScore: false,
            checkedHighScore: false,
            randomUuid: this.generateUuid(),
            highScores: [],
            renderTable: true
        }
    },
    mounted() {
        this.dynamoClient = new DynamoDBClient({ region: this.region, credentials: this.getCreds() });
        this.getHighScores(this);
    },
    methods: {
        generateUuid() {
            return 'xxxxxxxxxxxx'.replace(/[x]/g, function (c) {
                var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0xf | 0x0);
                return v.toString(16);
            });
        },
        showInput() {
            this.newHighScore = !this.newHighScore;
        },
        async getCreds() {
            const session = await fetchAuthSession();
            return session.credentials;
        },
        restart() {
            this.$router.push({ path: '/' });
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
        async getHighScores() {
            const highScoresQuery = new QueryCommand({
                TableName: this.tableName,
                IndexName: this.scoreIndexName,
                Limit: this.numberOfHighScores,
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
            if (!this.checkedHighScore) {
                this.checkIfNewHighScore();
                this.checkedHighScore = true;
            }
        },
        checkIfNewHighScore() {
            if (this.highScores.length < this.numberOfHighScores) {
                this.newHighScore = true;
                return;
            }
            for (const scoreItem of this.highScores) {
                if (this.score > parseInt(scoreItem.score.N)) {
                    this.newHighScore = true;
                    return;
                }
            }
        },
        async addHighScore() {
            const putItem = new PutItemCommand({
                TableName: this.tableName,
                Item: {
                    "id": { "S": this.randomUuid.toString() },
                    "name": { "S": this.sanitizeInput(this.highScoreName) },
                    "initialScore": { "N": this.score.toString() },
                    "accuracy": { "N": this.accuracy.toString() },
                    "score": { "N": ((this.accuracy / 100) * this.score).toString() },
                    "category": { "S": this.topic },
                    "sortID": { "N": "1" } // Used for index to query based on score
                }
            });
            const response = await this.dynamoClient.send(putItem);
            this.newHighScore = false;
            this.saveAllScores = false;
            this.getHighScores();
        }

    }
}
</script>