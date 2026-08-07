const { Client, GatewayIntentBits, PermissionFlagsBits } = require('discord.js');
const express = require('express');

// --- สร้างเว็บเซิร์ฟเวอร์จำลองเพื่อให้ UptimeRobot พิงค์ (แก้สถานะ Down เป็น Up) ---
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
    res.send('🤖 Bot is running 24/7!');
});

app.listen(PORT, () => {
    console.log(`🌍 Web server is listening on port ${PORT}`);
});
// --------------------------------------------------------------------------------

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildVoiceStates
    ]
});

const PREFIX = '!';
const OWNER_ID = '1534608114614272162'; // อย่าลืมใส่ User ID ของคุณ

client.once('ready', () => {
    console.log(`🤖 บอทออนไลน์แล้วในชื่อ: ${client.user.tag}`);
});

client.on('messageCreate', async (message) => {
    if (message.author.bot || !message.content.startsWith(PREFIX)) return;

    const args = message.content.slice(PREFIX.length).trim().split(/ +/);
    const command = args.shift().toLowerCase();
    const voiceChannel = message.member.voice.channel;

    if (command === 'muteall' || command === 'unmuteall') {
        if (message.author.id !== OWNER_ID) {
            return message.reply('🚫 คำสั่งนี้ใช้ได้เฉพาะเจ้าของบอทเท่านั้น!');
        }

        if (!voiceChannel) {
            return message.reply('❌ คุณต้องอยู่ในห้องเสียง (Voice Channel) ก่อนใช้คำสั่งนี้!');
        }

        try {
            let count = 0;

            if (command === 'muteall') {
                for (const [memberID, member] of voiceChannel.members) {
                    if (!member.user.bot && !member.voice.serverMute && member.id !== message.author.id) {
                        await member.voice.setMute(true, 'สั่ง Mute ทั้งห้องโดยเจ้าของบอท');
                        count++;
                    }
                }
                message.channel.send(`🔇 **ปิดเสียงทุกคนในห้อง ${voiceChannel.name} เรียบร้อยแล้ว!** (${count} คน) *[ยกเว้นตัวคุณเอง]*`);
            } 
            else if (command === 'unmuteall') {
                for (const [memberID, member] of voiceChannel.members) {
                    if (!member.user.bot && member.voice.serverMute) {
                        await member.voice.setMute(false, 'สั่ง Unmute ทั้งห้องโดยเจ้าของบอท');
                        count++;
                    }
                }
                message.channel.send(`🔊 **เปิดเสียงทุกคนในห้อง ${voiceChannel.name} เรียบร้อยแล้ว!** (${count} คน)`);
            }
        } catch (error) {
            console.error(error);
            message.reply('⚠️ เกิดข้อผิดพลาดในการจัดการเสียงสมาชิก (โปรดเช็กสิทธิ์/ยศของบอท)');
        }
    }
});

client.login(process.env.TOKEN);