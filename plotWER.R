packages <- c('tidyverse', 'forcats', 'ggraph','tidygraph','readxl')
ipak <- function(pkg){
  new.pkg <- pkg[!(pkg %in% installed.packages()[, 'Package'])]
  if (length(new.pkg))
    install.packages(new.pkg, dependencies = TRUE)
  sapply(pkg, require, character.only = TRUE)
}

ipak(packages)

data <- read_csv('compareMics.csv') %>%
  mutate(pct_ins = 100*insertions/transcript_wordcount, 
         pct_del = 100*deletions/transcript_wordcount, 
         pct_sub = 100*substitutions/transcript_wordcount )

ggplot(data, aes(x=session, y=wer, color=mic))+
  geom_point(position=position_jitterdodge())+
  geom_boxplot(outlier.shape = NA)+
  scale_y_continuous(limits = c(0, 1.6))
  
ggplot(data, aes(x=session, y=pct_ins, color=mic))+
  geom_point(position=position_jitterdodge())+
  geom_boxplot()+
  scale_y_continuous(limits = c(0, 100))

ggplot(data, aes(x=session, y=pct_del, color=mic))+
  geom_point(position=position_jitterdodge())+
  geom_boxplot()

ggplot(data, aes(x=session, y=pct_sub, color=mic))+
  geom_point(position=position_jitterdodge())+
  geom_boxplot()
