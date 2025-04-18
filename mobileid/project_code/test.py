import http.client

if __name__ == '__main__':

    conn = http.client.HTTPSConnection("shib.ucmerced.edu")
    payload = ''
    headers = {
      'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
      'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
      'cache-control': 'no-cache',
      'dnt': '1',
      'pragma': 'no-cache',
      'priority': 'u=0, i',
      'sec-ch-ua': '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
      'sec-ch-ua-mobile': '?0',
      'sec-ch-ua-platform': '"macOS"',
      'sec-fetch-dest': 'document',
      'sec-fetch-mode': 'navigate',
      'sec-fetch-site': 'none',
      'sec-fetch-user': '?1',
      'upgrade-insecure-requests': '1',
      'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',
      'Cookie': '_scid=Ic_axybbNapcWu2KQbPQB0XUlkR3FPy2; _tt_enable_cookie=1; _ttp=01JN20PX96CN3HWEEDYE7SEZ03_.tt.1; _fbp=fb.1.1740603356486.499765120694379326; _mkto_trk=id:976-RKA-196&token:_mch-ucmerced.edu-bc9ac74da238b9517b062d67c0cf33be; _ga_ZNSTZ2YGVJ=GS1.1.1742529086.1.1.1742529115.0.0.0; _ga_12VFZGH5J2=GS1.2.1743837418.5.0.1743837418.0.0.0; _ga_TSE2LSBDQZ=GS1.1.1744166927.12.0.1744166927.60.0.0; _sctr=1%7C1744268400000; ttcsid_CSFURPRC77UC379F8IVG=1744350145449.1.1744350145653; _ScCbts=%5B%5D; _scid_r=NU_axybbNapcWu2KQbPQB0XUlkR3FPy2DKvtjQ; ttcsid=1744741212019.11.1744741212019; _uetvid=13366c10f48411efb8ba870ea856949e; ttcsid_C8LNTT0H473GVAFU5FV0=1744741212019.11.1744741215624; _ga=GA1.1.510264552.1740603356; _ga_MDV0RFSJ6H=GS1.1.1744741216.2.1.1744741420.0.0.0; __Host-JSESSIONID=6861C515165395D33D8E601A5C0188F4; AWSALB=lUZ9xZifLwpBFGAycITgJsFrcBP6kzUE8L9/GAC4NaERC6hPeRU6Ov3bKHTjCzSCkgAaSJd3iQ9K11RTc0f094fy8A3SMp7/AriE52tRgpA7aeoPVIobJLVnM4c6; AWSALBCORS=lUZ9xZifLwpBFGAycITgJsFrcBP6kzUE8L9/GAC4NaERC6hPeRU6Ov3bKHTjCzSCkgAaSJd3iQ9K11RTc0f094fy8A3SMp7/AriE52tRgpA7aeoPVIobJLVnM4c6; AWSALB=TcZMMko+Upl62X3+3veiTyTXg/KOsWtkVKGHaqPMOOO0vdPw65HpvgpiRznDHRbyRYQVo3SZIYrvHgCGRott7KzuQMSUVHMbgG48qSCo6gxP7IWF4MmDDA/fAHPu; AWSALBCORS=TcZMMko+Upl62X3+3veiTyTXg/KOsWtkVKGHaqPMOOO0vdPw65HpvgpiRznDHRbyRYQVo3SZIYrvHgCGRott7KzuQMSUVHMbgG48qSCo6gxP7IWF4MmDDA/fAHPu; __Host-JSESSIONID=8C436338E021CF856A1D1E6237D55E70'
    }
    conn.request("GET", "/idp/profile/cas/login?execution=e1s1", payload, headers)
    res = conn.getresponse()
    data = res.read(
    print(data.decode("utf-8"))