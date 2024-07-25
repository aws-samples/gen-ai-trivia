<template>
    <div class="gap-2 col-10 mt-5">
        <div>
            <img id="robot" src="../assets/happy_robot_smile_right.jpg" class="float-start" width="40%">
        </div>

        <div>
            <div class="card mb-4">
                <div id="message1" ref="message1" class="card-body">
                </div>
            </div>
            <div class="card mb-4">
                <div id="message2" ref="message2" class="card-body"></div>
            </div>
            <div id="submit-div" ref="startRound">
                <button @click="startTheRound" type="submit" class="btn btn-dark">Start Round {{ this.roundNumber
                    }}</button>
            </div>
        </div>
    </div>
</template>

<script>
import data from '../data.json'
export default {
    props: ['score'],
    data() {
        return {
            rounds: data.rounds
        }
    },
    emits: ['start-round'],
    props: ['topic', 'roundNumber'],
    async mounted() {
        this.$refs.startRound.style.display = "none";
        async function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }
        async function updateMessage(messageElement, message) {
            messageElement.insertAdjacentHTML('beforeend', '<p>');
            for (let i = 0; i < message.length; i++) {
                messageElement.insertAdjacentHTML('beforeend', message.charAt(i));
                await sleep(1);
            }
            messageElement.insertAdjacentHTML('beforeend', '</p>');
        }
        await updateMessage(this.$refs.message1, this.rounds[this.roundNumber - 1].messages[0]);
        for (let i = 1; i < this.rounds[this.roundNumber - 1].messages.length; i++) {
            await updateMessage(this.$refs.message2, this.rounds[this.roundNumber - 1].messages[i])
        }
        this.$refs.startRound.style.display = "block";
    },
    methods: {
        startTheRound() {
            this.$emit('start-round');
        }
    }
}
</script>