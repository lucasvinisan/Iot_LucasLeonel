from machine import Pin, I2C, PWM, RTC
import ssd1306
import ds18x20
import onewire
import time

# Configurações globais
ARQUIVO_CSV   = "temperaturas.csv" #Definido o arquivo CSV
SALVAR_A_CADA = 10 # A cada 10 leituras de temperaturas será salvo automaticamente

#  Inicialização dos dispotivos perifericos (Timestamp do RTC, Sensor, LEDs, Buzzers)
def inicializar():
    rtc = RTC()
    rtc.datetime((2026, 4, 23, 3, 10, 0, 0, 0))

    i2c  = I2C(0, scl=Pin(21), sda=Pin(22))
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)

    leds = {
        "verde":    Pin(16, Pin.OUT),
        "amarelo":  Pin(17, Pin.OUT),
        "vermelho": Pin(5,  Pin.OUT),
    }

    buzzer = PWM(Pin(0))
    buzzer.duty(0)

    rele = Pin(2, Pin.OUT)
    rele.value(0)

    ow   = onewire.OneWire(Pin(13))
    ds   = ds18x20.DS18X20(ow)
    roms = ds.scan()
    if not roms:
        raise RuntimeError("Sensor DS18B20 não encontrado!")

    return rtc, oled, leds, buzzer, rele, ds, roms



#  Função definida para realização da leitura do sensor de temperatura 
def ler_temperatura(ds, roms):
    ds.convert_temp()
    time.sleep_ms(750)
    return ds.read_temp(roms[0])



#  FUnção para a classificação para os status de temperatura 
def classificar_status(temp):
    if temp <= 40:
        return "Normal"
    elif temp <= 70:
        return "Alerta"
    else:
        return "PERIGO"


#  Função Timestamp do RTC
def obter_timestamp(rtc):
    d = rtc.datetime()
    return "{:04d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}".format(
        d[0], d[1], d[2], d[4], d[5], d[6]
    )


#  Função para atualização do display OLED
def atualizar_display(oled, temp, status, hora):
    oled.fill(0)
    oled.text("TEMPERATURA", 20, 0)
    oled.text("-" * 15, 5, 10)
    oled.text("Motor:{:.1f}C".format(temp), 0, 25)
    oled.text("Status:{}".format(status[:6]), 0, 40)
    oled.text(hora[11:], 0, 55)
    oled.show()


#Função de controle de LEDs, buzzer e relé

def controlar_atuadores(leds, buzzer, rele, status):
    for led in leds.values():
        led.value(0)
    buzzer.duty(0)
    rele.value(0)

    if status == "Normal":
        leds["verde"].value(1)
    elif status == "Alerta":
        leds["amarelo"].value(1)
    elif status == "PERIGO":
        leds["vermelho"].value(1)
        buzzer.freq(1000)
        buzzer.duty(512)
        rele.value(1)


# Função para realizar o salvamento da temperaturas em arquivo do tipo CSV

def inicializar_csv():
    with open(ARQUIVO_CSV, "w") as f:
        f.write("timestamp,temperatura,status\n")


def salvar_buffer(buffer):
    with open(ARQUIVO_CSV, "a") as f:
        for linha in buffer:
            f.write(linha)



#Função de finalização da simulação com funçãode imprimir os valores observados e imprimir mensagem no OLED   

def finalizar(oled, leds, buzzer, buffer):
    for led in leds.values():
        led.value(0)
    buzzer.duty(0)
    buzzer.deinit()

    if buffer:
        salvar_buffer(buffer)

    oled.fill(0)
    oled.text("Simulacao", 20, 20)
    oled.text("Concluida!", 20, 35)
    oled.show()

    print("Simulacao concluida! Arquivo: {}".format(ARQUIVO_CSV))

    with open(ARQUIVO_CSV, "r") as f:
        for linha in f:
            print(linha, end="")


# Função main principal (Onde todo a solução vai ser realizada)

def main():
    rtc, oled, leds, buzzer, rele, ds, roms = inicializar() #Inicializando os perifericos
    inicializar_csv() #Inicializando o arquivo CSV 

    buffer = []
    cont = 0

    #loop principal 
    while cont <= 100:
        temp      = ler_temperatura(ds, roms)
        status    = classificar_status(temp)
        timestamp = obter_timestamp(rtc)

        buffer.append("{},{:.1f},{}\n".format(timestamp, temp, status))

        if len(buffer) >= SALVAR_A_CADA:
            salvar_buffer(buffer)
            buffer = []

        atualizar_display(oled, temp, status, timestamp)
        controlar_atuadores(leds, buzzer, rele, status)

        # print("{} | Temp: {:.1f}C | {}".format(timestamp, temp, status))
        cont += 1

    finalizar(oled, leds, buzzer, buffer)


main()