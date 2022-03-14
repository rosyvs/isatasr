from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('/Users/roso8920/Dropbox (Emotive Computing)/iSAT/AudioPrepro/results/alignment_all_asr_segwise_VS_ELANtranscript_segwise_Crystal_21-11-18_si_l4_p4_Video_yeti9_5min.csv')


delwords = df[df['operation'] == 'del']['reference'].tolist()

wordcloud = WordCloud().generate(' '.join(delwords))

plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.show()



correctwords = df[df['operation'] == '=']['reference'].tolist()

wordcloud = WordCloud().generate(' '.join(correctwords))

plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.show()