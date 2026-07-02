import { Alert, TouchableOpacity, View,Text } from 'react-native'
import React, { useEffect, useRef, useState } from 'react'
import { StatusBar } from 'expo-status-bar'
import MessageList  from '@/components/MessageList'
import {MessageInterface} from '@/types/types';
import { widthPercentageToDP as wp, heightPercentageToDP as hp } from 'react-native-responsive-screen'
import { GestureHandlerRootView, TextInput } from 'react-native-gesture-handler'
import { Feather } from '@expo/vector-icons'
import {callChatBotAPI } from '@/services/chatBot'
import PageHeader from '@/components/PageHeader'
import {  useCart } from '@/components/CartContext'

const ChatRoom = () => {
  const {addToCart, emptyCart} = useCart();

  const [messages, setMessages] = useState<MessageInterface[]>([]);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const textRef = useRef('')
  const inputRef = useRef<TextInput>(null)

  useEffect(() => {
  }, [messages]);

  // Sends the given conversation to the bot and appends its reply. Extracted so a
  // failed request can be retried with the same input from the error dialog.
  const requestBotReply = async (inputMessages: MessageInterface[]) => {
    setIsTyping(true)
    try {
        const responseMessage = await callChatBotAPI(inputMessages);
        setIsTyping(false)
        setMessages(prevMessages => [...prevMessages, responseMessage]);

        if (responseMessage?.memory?.order) {
            emptyCart()
            responseMessage.memory.order.forEach((item: any) => {
                addToCart(item.item, item.quantity)
            });
        }
    } catch (err: any) {
        // Always clear the typing indicator (previously it stayed spinning on error).
        setIsTyping(false)
        Alert.alert(
            'Connection problem',
            "Sorry — I couldn't reach the assistant. Please try again.",
            [
                { text: 'Cancel', style: 'cancel' },
                { text: 'Retry', onPress: () => requestBotReply(inputMessages) },
            ]
        )
    }
  }

  const handleSendMessage = async () => {
    const message = textRef.current.trim();
    if (!message) return;

    // Add the user message to the list of messages
    const inputMessages: MessageInterface[] = [...messages, { content: message, role: 'user' }];
    setMessages(inputMessages);
    textRef.current = ''
    if (inputRef) inputRef?.current?.clear();

    await requestBotReply(inputMessages);
  }

  return (
    <GestureHandlerRootView>
        <StatusBar style='dark' />
        
        <View
            className='flex-1 bg-white'
        >

        <PageHeader title="Chat Bot" showHeaderRight={false} bgColor='white'/>
        
        <View className='h-3 border-b border-neutral-300' />

        <View
            className='flex-1 justify-between bg-neutral-100 overflow-visibile'
        >
            <View
                className='flex-1'
            >
                <MessageList 
                    messages={messages}
                    isTyping={isTyping}

                />
            </View>

            <View
                style={{marginBottom: hp(2.7)}}
                className='pt-2'
            >
                <View
                    className="flex-row mx-3 justify-between border p-2 bg-white border-neutral-300  rounded-full pl-5"
                >
                    <TextInput 
                        ref = {inputRef}
                        onChangeText={value => textRef.current = value}
                        placeholder='Type message...'
                        style={{fontSize: hp(2)}}
                        className='flex-1 mr2'
                    />
                    <TouchableOpacity
                        onPress = {handleSendMessage}
                        className='bg-neutral-200 p-2 mr-[1px] rounded-full'
                    >
                        <Feather name="send" size={hp(2.7)} color="#737373"/>
                    </TouchableOpacity>
                </View>
            </View>
        </View>



        </View>
    </GestureHandlerRootView>
  )
}

export default ChatRoom

