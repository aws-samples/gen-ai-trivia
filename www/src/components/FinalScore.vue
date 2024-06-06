<template>
    <div>
        <h1 class="display-5 text-center mt-5">Game Over</h1>
        <div class="gap-2 mt-5">
            <img id="happy-img" src="../assets/happy_robot_smile_right.jpg" class="float-start" width="30%">
            <div ref="message" class="card p-3 w-50 mt-5">
                <p>You made it through {{ roundNumber }} rounds with a final score of {{ score }} and accuracy of {{
                    accuracy }}%</p>
            </div>
            <div v-if="newTopScore" class="card mt-3 w-50 border-success">
                <div class="card-header bg-success text-white">
                    <p>Congrats!! Your score is in the top ten highest scores!</p>
                </div>
                <div class="card-body">
                    <p>Recored your score for future players to try to beat it!</p>
                    <input type="text" id="highScoreName" v-model="highScoreName" placeholder="Enter your name" />
                    <button class="btn btn-dark ms-2" type="submit" @click="addHighScore">Submit</button>
                </div>
            </div>
            <table class="table table-dark w-50 mt-3">
                <caption class="caption-top">Top 10 Scores</caption>
                <thead>
                    <tr>
                        <th scope="col">Name</th>
                        <th scope="col">Score</th>
                        <th scope="col">Accuracy</th>
                        <th scope="col">Adujsted Score for Accuracy</th>
                        <th scope="col">Category</th>
                    </tr>
                </thead>
                <tbody class="table-group-divider">
                    <tr v-for="scoreItem in topTenScores">
                        <td>{{ scoreItem.name.S }}</td>
                        <td>{{ scoreItem.initialScore ? scoreItem.initialScore.N : 'null' }}</td>
                        <td>{{ scoreItem.accuracy ? scoreItem.accuracy.N : 'null' }}%</td>
                        <td>{{ scoreItem.score.N }}</td>
                        <td>{{ scoreItem.category.S }}</td>
                    </tr>
                </tbody>
            </table>
            <div class="position-absolute start-50">
                <button class="btn btn-success btn-lg" @click="restart">Play Again?</button>
            </div>
        </div>
    </div>
</template>

<script>
import { DynamoDBClient, QueryCommand, PutItemCommand } from "@aws-sdk/client-dynamodb";
import { fetchAuthSession } from "aws-amplify/auth";
import data from '../data.json';

export default {
    props: ['topic', 'roundNumber', 'score', 'accuracy'],
    data() {
        return {
            region: data.region,
            highScoreName: '',
            tableName: data.highscores.table,
            topTenScores: [],
            newTopScore: false,
            checkedHighScore: false
        }
    },
    mounted() {
        this.dynamoClient = new DynamoDBClient({ region: this.region, credentials: this.getCreds() });
        this.getTop10Scores(this);
    },
    methods: {
        showInput() {
            this.newTopScore = !this.newTopScore;
        },
        async getCreds() {
            const session = await fetchAuthSession();
            return session.credentials;
        },
        async getTop10Scores(_this) {
            const topScoresQuery = new QueryCommand({
                TableName: this.tableName,
                KeyConditionExpression: "id = :i",
                ExpressionAttributeValues: { ":i": { "S": "1" } }, // Use same ID and sort on score. If ID needed later, need to create a score index with fake PK
                ScanIndexForward: false,
                Limit: 10
            });
            const response = await _this.dynamoClient.send(topScoresQuery);
            _this.topTenScores = response.Items;
            if (!_this.checkedHighScore) {
                _this.checkIfNewHighScore();
                _this.checkedHighScore = true;
            }
        },
        checkIfNewHighScore() {
            if (this.topTenScores.length >= 10) {
                const lowestScore = parseInt(this.topTenScores.slice(-1)[0].score.N);
                if (this.score > lowestScore) {
                    this.newTopScore = true;
                }
            } else {
                this.newTopScore = true;
            }
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
        async addHighScore() {
            const putItem = new PutItemCommand({
                TableName: this.tableName,
                Item: {
                    "id": { "S": "1" }, // Use same ID and sort on score. If ID needed later, need to create a score index with fake PK
                    "name": { "S": this.sanitizeInput(this.highScoreName) },
                    "initialScore": { "N": this.score.toString() },
                    "accuracy": { "N": this.accuracy.toString() },
                    "score": { "N": ((this.accuracy / 100) * this.score).toString() },
                    "category": { "S": this.topic }
                }
            });
            const response = await this.dynamoClient.send(putItem);
            this.newTopScore = false;
            this.getTop10Scores(this);
        }

    }
}
</script>